import datetime
import random
import string
import socket

from django.contrib.auth.models import User

from geppetto.settings import DATABASES

from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import GroupOverride
from geppetto.core.models import Master
from geppetto.core.models import Node
from geppetto.core.models import NodeRoleAssignment
from geppetto.core.models import Override
from geppetto.core.models import Role
from geppetto.core.models import RoleDesConfigParamAssignment

from geppetto.geppettolib import network


def get_or_create_node(node_fqdn):
    try:
        node = Node.get_by_name(node_fqdn)
    except:
        node = Node.create(node_fqdn)
        # Generate and assign a Host GUID
        host_guid = _generate_host_guid()
        param = ConfigClassParameter.get_by_name(
                                            ConfigClassParameter.HOST_GUID)
        Override.update_or_create_override(node, param, host_guid)
        # Assign default roles on node creation
        default_roles = Role.get_default_roles()
        NodeRoleAssignment.add_roles_to_node(node, default_roles)
        # determine if we can add celeryd on each worker. This is
        # possible only if the DB backend is != sqlite3
        if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            celery_role = Role.get_by_name(Role.CELERY_WORKER)
            NodeRoleAssignment.add_roles_to_node(node, [celery_role], True)
    return node


def _generate_host_guid():
    guid = [random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff)]
    guid_strings = map(lambda x: "%02x" % x, guid)
    return ':'.join(guid_strings)


def assign_and_configure_roles_to_node(node_fqdn, role_list, node_config=None):
    node = Node.get_by_name(node_fqdn)
    if node_config != None:
        for param_label, value in node_config.iteritems():
            param = ConfigClassParameter.get_by_name(param_label)
            Override.update_or_create_override(node, param, value)
    roles = [Role.get_by_name(role_name) for role_name in role_list]
    NodeRoleAssignment.add_roles_to_node(node, roles, True)


def model_reset():
    """Recover the database to a pristine state"""
    Node.objects.all().delete()
    master = Master.get_infrastructure_master()
    master.fqdn = 'master'
    master.promoted_date = datetime.datetime(2001, 1, 1, 0, 0, 0, 0)
    master.save()
    root = User.objects.get(username='root')
    root.last_login = datetime.datetime(2001, 1, 1, 0, 0, 0, 0)
    root.save()
    config = ConfigClassParameter.get_by_name(ConfigClassParameter.\
                                              VPX_LOGGING_COLLECTOR)
    config.default_value = 'localhost'
    config.save()


def model_init():
    """Set this host to be the Geppetto master"""
    master_hostname = network.get_hostname()
    Master.promote_node(master_hostname)
    master = get_or_create_node(master_hostname)
    Override.\
        update_or_create_override(master,
                                  ConfigClassParameter.get_by_name(
                                  ConfigClassParameter.VPX_LABEL_PREFIX),
                                  'Citrix OpenStack VPX')
    NodeRoleAssignment.\
        add_roles_to_node(master,
                          [Role.get_by_name(Role.RABBITMQ),
                           Role.get_by_name(Role.CELERY_WORKER),
                           Role.get_by_name(Role.CELERY_CAMERA)],
                           True)


def set_root_password(raw_password):
    root = User.objects.get(username='root')
    root.set_password(raw_password)
    root.save()


def create_swift_rings(hostnames):
    """This attempts to create the swift ring file on the master,
    given the specified hostnames of the swift object nodes."""
    # Resolve IPs
    # TODO - we should have this info in the facts
    ips = []
    for hostname in hostnames:
        ips.append(socket.gethostbyname(hostname))
    ips_str = string.join(ips, " ")

    # Assign Ring Builder Role: runs on this host
    node_fqdn = network.get_hostname()
    node = Node.get_by_name(node_fqdn)

    Override.update_or_create_override(node,
                            ConfigClassParameter.get_by_name(
                                         ConfigClassParameter.SWIFT_NODES_IPS),
                            ips_str)
    NodeRoleAssignment.add_roles_to_node(node,
                                         [Role.get_by_name(Role.RING_BUILDER)],
                                         True)
    return node_fqdn


def update_related_config_params(roles, node_fqdn):
    """Update all config values affected by the given worker type moving
    to a new node. Then restart all affected services.
    """
    affected_config_parms = []
    for role in roles:
        if role.description:
            affected_config_parms.extend(RoleDesConfigParamAssignment.\
                            get_param_labels_by_description(role.description))
    affected_config_parms = set(affected_config_parms)

    for param_label in affected_config_parms:
        ConfigClassParameter.set_config_parameter(param_label, node_fqdn)
        Override.update_overrides(ConfigClassParameter.\
                                                get_by_name(param_label))
        GroupOverride.update_overrides(ConfigClassParameter.\
                                                get_by_name(param_label))

    # restart appropriate services on the affected nodes or
    # track nodes whose CLI configuration require a refresh
    node_dict = {}
    details = ConfigClassParameter.\
                            get_details_for_params(affected_config_parms)
    for param_label in affected_config_parms:
        applies_to = details[param_label]['applies-to']
        for role_name in applies_to:
            role_name = str(role_name)
            affected_nodes = Node.get_fqdns_by_role(role_name)
            for n in affected_nodes:
                if n in node_dict and role_name not in node_dict[n]:
                    node_dict[n].append(role_name)
                elif n != node_fqdn:
                    node_dict[n] = [role_name]
            affected_nodes = Node.get_fqdns_by_role(role_name,
                                                    is_service=False)
            for n in affected_nodes:
                if n not in node_dict:
                    node_dict[n] = []

    svc_restart = ConfigClassParameter.\
                get_by_name(ConfigClassParameter.VPX_RESTART_SERVICES)
    for node_fqdn, role_to_restart in node_dict.iteritems():
        if len(role_to_restart) > 0:
            Override.update_or_create_override(Node.get_by_name(node_fqdn),
                                               svc_restart,
                                               role_to_restart,
                                               True)

    return node_dict.keys()
