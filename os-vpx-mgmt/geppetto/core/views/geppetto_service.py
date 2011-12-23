# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Citrix Systems, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from geppetto.core import Failure
from geppetto.tasks import task_utils
from geppetto.geppettolib import utils as trace_utils

from geppetto.core.models import utils as model_utils
from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Group
from geppetto.core.models import GroupOverride
from geppetto.core.models import Node
from geppetto.core.models import NodeRoleAssignment
from geppetto.core.models import Override
from geppetto.core.models import Role
from geppetto.core.models import RoleDescription

from geppetto.core.views import validators
from geppetto.core.views.xmlrpc import GenerateDjangoXMLRPCHandler2

logger = logging.getLogger('geppetto.core.views.geppetto_service')
trace = trace_utils.get_trace_decorator(logger)

# To expose a method to the API endpoint, please follow this naming convention:
# MainComponent___methodName
#
# The proxy method will be translated in MainComponent.methodName
#
# Private methods (ones that start with _) are excluded


class Service():
    """The Geppetto API (Experimental).

    (*) Means the call is implemented but it may not be thoroughly tested."""

    def __init__(self, new_logger):
        global logger
        logger = new_logger

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___get_all(self):
        """
        (*)
        Return list of labels for globally defined configuration parameters.

        return(list(string)): the list of configuration parameters.

        Example list is:
        ['HAPI_DRIVER', 'HAPI_USER','HAPI_PASS', ...]
        """
        return ConfigClassParameter.get_names()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___get_all_by_role(self, role_name):
        """
        (*)
        Return the list of labels for configuration parameters on which
        a role depends on.

        role_name(string): the name of the role
        return(list(string)): the labels for configuration parameters
        """
        role = Role.get_by_name(role_name)
        return role.get_config_labels()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___get_details(self, param_labels):
        """
        (*)
        Return dictionary of details for configuration parameters specified.

        param_labels(list(string)): parameters whose details need retrieving
        return(dict(str:dict)): the details dictionary

        Return dictionary of parameters's details; e.g:
        {'RABBIT_PASS': {'param-value': 'guest',
                         'param-description': 'The user password',
                         'applies-to': ['openstack-nova-api',
                                        'openstack-nova-compute',
                                        'openstack-nova-network',
                                        'openstack-nova-scheduler',
                                        'openstack-nova-volume'],
                        'param-type': 'string',
                        'config-description': "Stores credentials...",
                        'config-name': 'rabbitmq-config',}
            ...
        }
        """
        return ConfigClassParameter.get_details_for_params(param_labels)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___get(self, param_label):
        """
        (*)
        Return value for the specified config parameter.

        param_label(string): the label of the config parameter to get
        return(string): the value of the config parameter
        """
        return ConfigClassParameter.get_value_by_name(param_label)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___set(self, param_label, value):
        """
        (*)
        Update the value of the specified config parameter.

        param_label(string): the label of the config parameter to set
        value(string): the new value
        return(None)"""
        ConfigClassParameter.set_config_parameter(param_label, value)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___set_items(self, config):
        """
        Update all the specified configuration values.

        config(dict{string:string}): the configuration values to set
        return(None)"""
        for k, v in config.iteritems():
            ConfigClassParameter.set_config_parameter(k, v)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___add_node_overrides(self, node_fqdn,
                                   config_dict, onetime=False):
        """
        (*)
        Add multiple configuration overrides to the node.

        If the override already exists, it updates the value/

        node_fqdn(string): the node to override
        config_dict(dict): Dictionary with parameters to override
                           and their values
        onetime(boolean): if True, it gets removed once it applies to the node
        return(None)
        """
        node = Node.get_by_name(node_fqdn)
        for param_label in config_dict:
            param = ConfigClassParameter.get_by_name(param_label)
            Override.update_or_create_override(node, param,
                                               config_dict[param_label],
                                               onetime)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___add_node_override(self, node_fqdn,
                                   param_label, value, onetime=False):
        """
        (*)
        Add a configuration override to the node.

        If the override already exists, it updates the value/

        node_fqdn(string): the node to override
        param_label(string): the configuration to override
        value(string): the new value
        onetime(boolean): if True, it gets removed once it applies to the node
        return(None)
        """
        node = Node.get_by_name(node_fqdn)
        param = ConfigClassParameter.get_by_name(param_label)
        Override.update_or_create_override(node, param, value, onetime)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___remove_node_override(self, node_fqdn, param_label):
        """
        (*)
        Remove the override from the node configuration.

        node_fqdn(string): the node
        param_label(string): the param to be removed from node configuration
        return(None)
        """
        node = Node.get_by_name(node_fqdn)
        param = ConfigClassParameter.get_by_name(param_label)
        Override.remove_override(param, node)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___create_override_group(self, group_name):
        """
        (*)
        Create a new override group named group_name.

        group_name(string): the group name. No duplicates are allowed
        return(None)
        """
        Group.create(group_name)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___delete_override_group(self, group_name):
        """
        (*)
        Delete the override group named group_name.

        All nodes assigned to this override group will get their group
        set to None.

        group_name(string): the group_name. The group must exist
        return(None)
        """
        Group.delete_by_name(group_name)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___get_override_group_details(self, group_name):
        """
        (*)
        Return dictionary D of group overrides plus the list of nodes
        assigned to the group.

        group_name: the group
        return(dict of dict): the dictioanry containing the group details

        Example D is:
        {'overrides': {'HAPI_PASS': 'test_pass',
                       'HAPI_USER': 'test_user',}
         'nodes: ['node1_fqdn', 'node2_fqdn', ...]}
        """
        details = {}
        group = Group.get_by_name(group_name)
        details['overrides'] = group.get_overrides_dict()
        details['nodes'] = group.get_node_fqdns()
        return details

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___has_override_group(self, group_name):
        """
        (*)
        Tells whether a specific override group is defined in the current
        configuration

        group_name: the group
        return(boolean): True if the Group exists, False otherwise

        """
        group = Group.get_all_by_name(group_name)
        return len(group) == 1

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___add_group_override(self, group_name, param_label, value):
        """
        (*)
        Add a configuration override to the group.

        group_name(string): the group to override
        param_label(string): the configuration to override
        value(string): the new value
        return(None)
        """
        group = Group.get_by_name(group_name)
        GroupOverride.create(group, param_label, value)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___remove_group_override(self, group_name, param_label):
        """
        (*)
        Remove the override from the group configuration.

        group_name(string): the group
        param_label(string): the param to be removed from the group override
        return(None)
        """
        group = Group.get_by_name(group_name)
        param = ConfigClassParameter.get_by_name(param_label)
        GroupOverride.remove_override(group, param)

    @trace
    def Config___add_nodes_to_override_group(self, node_fqdns, group_name):
        """
        (*)
        Add one or more nodes to the override group.

        node_fqdns(list): list of node_fqdn(s)
        group_name(string): the name of the group to which associate nodes
        return(None)
        """
        failures = []
        messages = []
        group = Group.get_by_name(group_name)
        for node_fqdn in node_fqdns:
            try:
                node = Node.get_by_name(node_fqdn)
                node.set_group(group)
            except Failure, f:
                failures.append(f)
                messages.append('Cannot add node %(node_fqdn)s ' \
                                'to %(group_name)s' % locals())
        if len(failures) > 0:
            raise Failure('add_nodes_to_override_group',
                          'Config',
                          ','.join(messages),
                          failures)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Config___remove_node_from_override_group(self, node_fqdn, group_name):
        """
        (*)
        Remove node from the override group.

        node_fqdn(string): to node to which group overrides should be removed
        group_name(string): the name of the group, the node is associated to
        return(None)
        """
        group = Group.get_by_name(group_name)
        node = Node.get_by_name(node_fqdn)
        node.unset_group(group)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Node___get_all(self):
        """
        (*)
        Return fqdn(s) of nodes available in the infrastructure zone.

        return(list(string)): the fqdns of nodes available in the zone"""
        return Node.get_fqdns()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Node___get_details(self, node_fqdns):
        """Return details for the nodes whose fqdns are specified. It silently
        ignores nodes that are not found.

        node_fqdns(list(string)): the fqdns whose details need retrieving
        return(dict(str:dict)): the details dictionary

        Return dictionary of node details; e.g:
        {
        'os-vpx-00-11-22-33-44-55.openstack.com':
            { 'roles': ['openstack-nova-api', 'openstack-dashboard', ...],
              'host_fqdn': 'xs1.example.org',
              'master_fqdn': 'master.openstack.com',
              'management_ip': 192.168.1.200,
              'node_overrides': {...},
              'group_overrides': {...},
              ...
          'os-vpx-AA-BB-CC-DD-EE-FF.openstack.com': { ... }
          ...
        }
        """
        all_fqdns = Node.get_fqdns()
        all_fqdns.extend(Node.get_fqdns(is_enabled=False))
        return dict([(x, Node.get_by_name(x).get_details()) \
                                        for x in node_fqdns if x in all_fqdns])

    def Node___create(self, host_fqdn, config):
        """Create a node on a specific hypervisor host. Config is a  dictionary
        that contains the configuration for the VPX. Returns a task's id. The
        task's result will contain the fqdn of the newly created VPX node.

        host_fqdn(string): the fqdn for the host
        config(dict{string:string}): the configuration for the VPX
        return(string): the task id of the operation

        Example dictionary for config is:
        {'data-disk-size': '500',  # in MiB
         'management-bridge': 'xenbr0',
         'external-bridge': 'xenbr1',
         'boot-options': '',
         'max-memory': '1024', # om MiB
         'ballooning: 'True',}
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Node___copy(self, node_fqdn_src, node_fqdn_dst):
        """
        (*)
        Migrate all roles from the source node to teh destination node.
        This includes updating config values that are affected by this move,
        and restarting affective services so they notice the change.

        node_fqdn_src(string): the fqdn for the source host
        node_fqdn_dst(string): the fqdn for the destination host
        return(string): the task id of the operation
        """
        node_src = Node.get_by_name(node_fqdn_src)
        node_dst = Node.get_by_name(node_fqdn_dst)

        node_dst.set_group(node_src.get_group())
        Override.copy_node_overrides(node_dst, node_src.get_overrides())
        roles = NodeRoleAssignment.copy_role_assignments_to_node(
                                    node_src.get_role_assignments(), node_dst)

        node_src.unset_group(None)
        node_src.delete_overrides()
        node_src.delete_roles()
        node_src.disable()

        affected_node_fqdns = \
            model_utils.update_related_config_params(roles, node_fqdn_dst)

        if node_fqdn_dst not in affected_node_fqdns:
            affected_node_fqdns.append(node_fqdn_dst)
        return {'node_fqdns': affected_node_fqdns,
                'roles': [role.name for role in roles]}

    def Node___forget(self, node_fqdn):
        """Remove the specified node from the infrastructure and reflect
        changes in compute and storage fabric. The Node is still reachable
        on the network but is no longer part of the infrastructure being
        managed by the VPX Master. As an effect of the operation, the node
        will no longer auto-register with the VPX master.

        node_fqdn(string): the VPX node to be forgotten
        return(string): the task id of the operation
        """
        raise NotImplementedError()

    def Node___destroy(self, node_fqdn):
        """This is like Node.forget but it also uninstall the VPX node
        from the hypervisor host.

        node_fqdn(string): the VPX node to be destroyed
        return(string): the task id of the operation
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Node___get_by_role(self, role_name):
        """
        (*)
        Get a list of node_fqdn in the specified role.

        role_name(string): name of the role
        return(list(string)): fqdn(s) of nodes in the specified role"""
        return Node.get_fqdns_by_role(role_name)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Node___exclude_by_roles(self, role_names):
        """
        (*)
        Get a list of fqdn of nodes that do not run role_names.

        role_name(list(string)): names of the roles
        return(list(string)): fqdn(s) of nodes in the specified role"""
        return Node.get_fqdns_excluded_by_roles(role_names)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Node___get_by_roles(self, role_names):
        """
        (*)
        Get a list of node_fqdn in the specified role set.

        role_name(list(string)): names of the roles
        return(list(string)): fqdn(s) of nodes in the specified set of roles"""
        return Node.get_fqdns_by_roles(role_names)

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Node___restart_services(self, node_fqdn, service_names):
        """Restarts the specified services on the specified node.

        node_fqdn(string): the VPX node_fqdn
        service_names(list(string)): the names of the services to be restarted
        return(string): task_id of the operation
        """
        node = Node.get_by_name(node_fqdn)
        param = ConfigClassParameter.\
                        get_by_name(ConfigClassParameter.VPX_RESTART_SERVICES)
        Override.update_or_create_override(node, param, service_names, True)
        return {'node_fqdns': [node_fqdn]}

    def Host___get_all(self):
        """Return fqdn(s) of hosts in the infrastructure zone.

        return(list(string)): the fqdns of hosts in the zone"""
        raise NotImplementedError()

    def Host___get_details(self, host_fqdns):
        """Return dictionary of host details; e.g:

        { 'xs1.example.org':
             {'address': '192.168.0.1',
              'software_version': {'product_version': 'x.y.z',},
              'cpu_info': {'cpu_count': '16',},
              'metrics': {'memory_total': '34349113344',
                          'memory_free': '28237160448',},
              'local_storage': {'physical_size': '65145929728',
                                'physical_utilisation: '4194304',},
            }
          ...
        }
        """
        raise NotImplementedError()

    def Infrastructure___get_child_zones(self):
        """Return the list of zone descriptors; e.g.:

        [{'zone': 'zone_a',
          'master': 'https://192.168.1.1:8080/openstack/geppetto/v1',
         },
         {'zone': 'zone_b',
          'master': 'https://192.168.1.1:8080/openstack/geppetto/v2',
         },
        ...]
        """
        raise NotImplemented()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Role___get_service_roles(self):
        """
        (*)
        Return list of strings representing service roles.

        return(list(string)): list of all service roles. e.g.
        ["openstack-nova-api","openstack-nova-compute",...]
        """
        return list(Role.get_service_roles())

    @trace
    @validators.xmlrpc_fault_wrapper
    def Role___get_roles_details(self, is_service=True, is_internal=False):
        """
        (*)
        """
        return Role.get_roles_dict(is_service, is_internal)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Role___get_compositions(self):
        """
        (*)
        """
        return RoleDescription.get_compositions()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Role___has_node(self, role_name):
        """
        (*)
        return(bool): true if >=1 nodes are in role_name."""
        Role.get_by_name(role_name)
        return len(Node.get_all_by_rolename(role_name)) > 0

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def ObjectStorage___add_workers(self, node_fqdns, config):
        """
        (*)
        Add workers to the Object Storage fabric. More precisely, each node
        in node_fqdns gets the configuration 'config' and the following roles
        are started:

        *openstack-swift-account*
        *openstack-swift-container*
        *openstack-swift-object*
        *openstack-swift-rsync*

        node_fqdns(list(string)): list of the nodes to turn into workers
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *SWIFT_HASH_PATH_SUFFIX*
            String of the hash path suffix for swift. Default: 'citrix'.

        *SWIFT_DISKSET_COUNT*
            Integer number of disks to be plugged into the node. Default: 2.

        *SWIFT_DISK_SIZE_GB*
            Integer expressing the size of the disk. Default: 10GB.
        """
        # This does not currently honour the spec as:
        # - not all configs are treated
        # - we don't regenerate rings if this is called
        #   multiple times with different node_fqdns
        if len(node_fqdns) != len(set(node_fqdns)):
            raise Failure('NodeList', 'ObjectStorage.add_workers',
                          ('Duplicates in list %s' % node_fqdns))

        storage_node_services = [Role.SWIFT_ACCOUNT,
                                 Role.SWIFT_CONTAINER,
                                 Role.SWIFT_OBJECT,
                                 Role.SWIFT_RSYNC]
        disk_size = config.get(ConfigClassParameter.SWIFT_DISK_SIZE_GB, None)
        if disk_size is None:
            raise Failure('NodeList', 'ObjectStorage.add_workers',
                  ('Missing configuration %s' % ConfigClassParameter.\
                                                          SWIFT_DISK_SIZE_GB))

        node_config = {ConfigClassParameter.SWIFT_DISK_SIZE_GB: disk_size}
        for node_fqdn in node_fqdns:
            model_utils.assign_and_configure_roles_to_node(node_fqdn,
                                                       storage_node_services,
                                                       node_config)

        rings_node = model_utils.create_swift_rings(node_fqdns)
        node_fqdns.append(rings_node)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': storage_node_services}

    def ObjectStorage___delete_workers(self, node_fqdns):
        """Remove storage workers from the Object Storage fabric. As a result,
        services running on the node (because of a previous add_workers call)
        stop, and the configuration is cleaned-up, where appropriate.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def ObjectStorage___update_worker(self, node_fqdn, config):
        """Update the configuration for the worker (add/remove disks).

        Worker's service roles may need to restart to apply the configuration
        change. If unable to do so, the task result contains details about
        the operation.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Configuration parameters:

        *SWIFT_DISKSET_COUNT*
            Integer number of disks to be plugged into the node; Required.
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def ObjectStorage___add_apis(self, node_fqdns, config):
        """
        (*)
        Add API endpoints to the Object Storage fabric. More precisely,
        each node in node_fqdns gets the configuration 'config' and the
        following roles are started:

        *memcached*
        *openstack-swift-proxy*

        node_fqdns(list(string)): list of the nodes to turn into API nodes
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *SWIFT_API_BIND_HOST*
            String value for the interface on which the service roles
            should be listening. Default '0.0.0.0'.

        *SWIFT_API_BIND_PORT*
            Integer value for the port to be used. Default '443'.

        *SWIFT_HASH_PATH_SUFFIX*
            String of the hash path suffix for swift. Default: 'citrix'.
        """
        # This does not currently honour the spec as:
        # - not all configs are treated
        # - it does not support the addition of multiple nodes
        #   at the same time
        node_fqdn = node_fqdns[0]

        proxy_node_services = [Role.SWIFT_MEMCACHE,
                               Role.SWIFT_PROXY]
        model_utils.assign_and_configure_roles_to_node(node_fqdn,
                                                       proxy_node_services)

        self.Config___set(ConfigClassParameter.SWIFT_PROXY_ADDRESS, node_fqdn)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': proxy_node_services}

    def ObjectStorage___delete_apis(self, node_fqdns):
        """Remove API endpoints from the Object Storage fabric. As a result,
        services running on the node (because of a previous add_apis call)
        stop, and the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def ObjectStorage___update_api(self, node_fqdn, config):
        """Update the configuration for the API node (change host:port bind).

        API node's service roles may need to restart to apply the configuration
        change. If unable to do so, the task result contains details about the
        operation.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Configuration parameters:

        *SWIFT_API_BIND_HOST*
            String value for the interface on which the service roles
            should be listening. Default '0.0.0.0'.

        *SWIFT_API_BIND_PORT*
            Integer value for the port to be used. Default '443'.
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Identity___add_auth(self, node_fqdn, config):
        """Not implemented"""
        # TODO - temp implementation going in here
        roles = [Role.KEYSTONE_AUTH, Role.KEYSTONE_ADMIN]
        model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)
        self.Config___set(ConfigClassParameter.KEYSTONE_HOST, node_fqdn)

        return {'node_fqdns': [node_fqdn],
                'config_params': config.keys(),
                'roles': roles}

    def Identity___delete_auth(self, node_fqdn):
        """Not implemented"""
        raise NotImplementedError()

    def Identity___update_auth(self, node_fqdn, config):
        """Not implemented"""
        raise NotImplementedError()

    def Identity___add_admin(self, node_fqdn, config):
        """Not implemented"""
        raise NotImplementedError()

    def Identity___delete_admin(self, node_fqdn):
        """Not implemented"""
        raise NotImplementedError()

    def Identity___update_admin(self, node_fqdn, config):
        """Not implemented"""
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Compute___add_message_queue(self, node_fqdn, config={}):
        """
        (*)
        Add message queue to the Compute fabric. More precisely, the node
        'node_fqdn' gets the configuration 'config', and the roles below
        are started. The queue node becomes 'known' in the Compute fabric,
        meaning that services dependent on it (i.e. roles applied to other
        nodes in the compute fabric) may be restarted or may need a restart.
        The task object associated with the operation may contain information
        in this regard.

        *rabbitmq*

        node_fqdn(string): the node to turn into a message queue
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *None*
        """
        validators.validate_config(config, {})

        roles = [Role.RABBITMQ]
        model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)
        self.Config___set(ConfigClassParameter.RABBIT_HOST, node_fqdn)

        return {'node_fqdns': [node_fqdn],
                'config_params': config.keys(),
                'roles': roles}

    def Compute___delete_message_queue(self, node_fqdn):
        """Remove message queue from the Compute fabric. As a result, services
        running on the node (because of a previous add_message_queue call) stop
        and the configuration is cleaned-up.

        node_fqdn(string): node to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Compute___add_database(self, node_fqdn, config):
        """
        (*)
        Add a database to the Compute fabric. More precisely, the node
        'node_fqdn' gets the configuration 'config', and the roles below
        are started. The database node becomes 'known' in the Compute fabric,
        meaning that services dependent on it (i.e. roles applied to other
        nodes in the compute fabric) may be restarted or may need a restart.
        The task object associated with the operation may contain information
        in this regard.

        *mysqld*

        node_fqdn(string): the node to turn into a database
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *MYSQL_USER*
            String representing the user to be provisioned. Default 'root'.

        *MYSQL_PASS*
            String representing the password to be set for the user MYSQL_USER.
        """
        validators.validate_config(config,
                                   {ConfigClassParameter.MYSQL_PASS:
                                        [validators.config_required],
                                    ConfigClassParameter.MYSQL_USER: []})

        roles = [Role.MYSQL]
        model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)
        config[ConfigClassParameter.MYSQL_HOST] = node_fqdn
        for param_label, value in config.iteritems():
            self.Config___set(param_label, value)

        return {'node_fqdns': [node_fqdn],
                'config_params': config.keys(),
                'roles': roles}

    def Compute___delete_database(self, node_fqdn):
        """Remove the database from the Compute fabric. As a result, services
        running on the node (because of a previous add_database call) stop
        and the configuration is cleaned-up.

        node_fqdn(string): node to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Compute___add_apis(self, node_fqdns, config):
        """
        (*)
        Add API endpoints to the Compute fabric. More precisely, each node
        in node_fqdns gets the configuration 'config' and the following roles
        are started:

        *openstack-nova-api*
        *openstack-dashboard*

        node_fqdns(list(string)): list of the nodes to turn into API nodes
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *NOVA_API_BIND_HOST*
            String value for the interface on which the service roles
            should be listening. Default '0.0.0.0'.

        *NOVA_EC2_BIND_PORT*
            Integer value for the port to be used. Default '8773'.

        *NOVA_OSAPI_BIND_PORT*
            Integer value for the port to be used. Default '8774'.
        """
        # TODO - should we separate out the dashboard?
        roles = [Role.NOVA_API, Role.OPENSTACK_DASHBOARD]
        for node_fqdn in node_fqdns:
            model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)
            # TODO - this only works with a single node
            self.Config___set(ConfigClassParameter.COMPUTE_API_HOST, node_fqdn)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': roles}

    def Compute___delete_apis(self, node_fqdns):
        """Remove API endpoints from the Compute fabric. As a result, services
        running on the node (because of a previous add_apis call) stop, and
        the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def Compute___update_api(self, node_fqdn, config):
        """Update the configuration for the API node (change host:port bind).

        API node's service roles may need to restart to apply the configuration
        change. If unable to do so, the task result contains details about the
        operation.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Configuration parameters:

        *NOVA_API_BIND_HOST*
            String value for the interface on which the service roles
            should be listening. Default '0.0.0.0'.

        *NOVA_EC2_BIND_PORT*
            Integer value for the port to be used. Default '8773'.

        *NOVA_OSAPI_BIND_PORT*
            Integer value for the port to be used. Default '8774'.
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Compute___add_workers(self, node_fqdns, config):
        """
        (*)
        Add workers to the Compute fabric. More precisely, each node in
        node_fqdns gets the configuration 'config' and the following roles
        are started:

        *openstack-nova-compute*

        node_fqdns(list(string)): list of the nodes to turn into workers
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *GUEST_NETWORK*
            String that specifies the name of the network on which VMs
            will connect to. Default: 'xenbr0'. Flat networking only.

        *COMPUTE_VLAN_INTERFACE*
            String that specifies the interface to be used for VLAN
            connectivity. Default: 'eth1'. Vlan networking only.
        """
        #TODO: everything :(
        roles = [Role.NOVA_COMPUTE]
        # MULTI_HOST in config will tell us if we want to do HA networking
        # In this case each compute worker must be a network worker as well
        # Also, the NETWORK_WORKERS group override should be applied to
        # these nodes
        multi_host = self.Config___get(ConfigClassParameter.MULTI_HOST)
        # FIXME: is this safe?
        multi_host = multi_host == 'True'

        if multi_host:
            roles.append(Role.NOVA_NETWORK)

        for node_fqdn in node_fqdns:
            if multi_host and self.Config___has_override_group(
                                   GroupOverride.NETWORK_WORKERS):
                self.Config___add_nodes_to_override_group(
                     [node_fqdn], GroupOverride.NETWORK_WORKERS)
            model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': roles}

    def Compute___delete_workers(self, node_fqdns):
        """Remove workers from the Compute fabric. As a result, services
        running on the node (because of a previous add_workers call) stop,
        and the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def Compute___update_worker(self, node_fqdn, config):
        """Warning: Not Implemented"""
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Compute___add_ajax_console_proxies(self, node_fqdns, config):
        """
        Add the *openstack-nova-ajax-console-proxy* role to each node in
        node_fqdns, and apply the given configuration.

        node_fqdns(list(string)): list of the nodes to turn into ajax console
                                  proxy nodes
        config(dict): the configuration dictionary
        return(string): the uuid of the task operation

        Configuration parameters:

        *NOVA_AJAX_CONSOLE_PROXY_BIND_INTERFACE*
            The interface on which the service should be listening.
            Default '0.0.0.0'.
            *Unimplemented by OpenStack today*.

        *NOVA_AJAX_CONSOLE_PROXY_BIND_PORT*
            Integer value for the port to be used. Default '8000'.

        *NOVA_AJAX_CONSOLE_PUBLIC_URL*
            The publicly visible URL used to access consoles.  May be the
            special string 'auto' in which case this will be inferred from
            node_fqdns[0] and NOVA_AJAX_CONSOLE_PROXY_BIND_PORT.
            Default 'auto'.
        """
        bi = 'NOVA_AJAX_CONSOLE_PROXY_BIND_INTERFACE'
        bp = 'NOVA_AJAX_CONSOLE_PROXY_BIND_PORT'
        url = 'NOVA_AJAX_CONSOLE_PUBLIC_URL'
        c_url = 'NOVA_AJAX_CONSOLE_PUBLIC_URL_COMPUTED'

        roles = [Role.NOVA_AJAX_CONSOLE_PROXY]
        for node_fqdn in node_fqdns:
            model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)

        pub_url = config.get(url, ConfigClassParameter.get_value_by_name(url))
        if pub_url == 'auto' and len(node_fqdns) > 0:
            host = node_fqdns[0]
            port = config.get(bp, ConfigClassParameter.get_value_by_name(bp))
            config[c_url] = 'http://%s:%s' % (host, port)
        else:
            config[c_url] = pub_url

        self.Config___set_items(config)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': roles}

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Scheduling___add_workers(self, node_fqdns, config):
        """
        (*)
        Add a scheduler to on the specified nodes. To do this it will add
        the following roles to the specified nodes:

        *openstack-nova-scheduler*

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Currently there are no supported configuration settings.
        """
        # TODO - look at letting user chose which scheduler is used?
        roles = [Role.NOVA_SCHEDULER]
        for node_fqdn in node_fqdns:
            model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': roles}

    def Scheduling___delete_workers(self, node_fqdns):
        """Remove workers from the Scheduling fabric. As a result, services
        running on the node (because of a previous add_workers call) stop,
        and the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def Scheduling___update_worker(self, node_fqdn, config):
        """Updates the configuration and restartes the schedulers that are
        running on the specified nodes.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        However, currently there are no supported configuration settings.
        """
        raise NotImplemented()

    def _get_network_mode_config(self, mode, config):
        #Note: this does not have be an instance method
        #FlatDHCP choice also implies redefining GUEST_NETWORK_BRIDGE
        #global config parameter
        default_bridge_interface = self.Config___get(
                                   ConfigClassParameter.BRIDGE_INTERFACE)
        default_guest_nw_bridge = self.Config___get(
                                  ConfigClassParameter.GUEST_NETWORK_BRIDGE)
        stored_config_options = {
            "flat": {
               ConfigClassParameter.NETWORK_MANAGER:
                  "nova.network.manager.FlatManager"},
            "flatdhcp": {
               ConfigClassParameter.NETWORK_MANAGER:
                  "nova.network.manager.FlatDHCPManager",
               ConfigClassParameter.GUEST_NETWORK_BRIDGE:
                  config.get(ConfigClassParameter.GUEST_NETWORK_BRIDGE,
                             default_guest_nw_bridge),
               ConfigClassParameter.BRIDGE_INTERFACE:
                  config.get(ConfigClassParameter.BRIDGE_INTERFACE,
                             default_bridge_interface)},
            "vlan": {
               ConfigClassParameter.NETWORK_MANAGER:
                  "nova.network.manager.VlanManager",
               ConfigClassParameter.BRIDGE_INTERFACE:
                  config.get(ConfigClassParameter.BRIDGE_INTERFACE,
                             default_bridge_interface)},
            }
        return stored_config_options[mode]

    def _prepare_overrides(self, mode, config):
        """ Defines overrides to be applied to a node or a group
            1) GUEST_NW_VIF_MODE
            2) GUEST_NW_VIF_IP (optional)
            3) GUEST_NW_VIF_NETMASK (optional)
        """
        overrides = {}
        if mode in ("vlan", "flatdhcp"):
            eth2_mode = config[ConfigClassParameter.GUEST_NW_VIF_MODE]
            overrides[ConfigClassParameter.GUEST_NW_VIF_MODE] = eth2_mode
            if eth2_mode == "static" and not 'MULTI_HOST' in config:
                overrides[ConfigClassParameter.GUEST_NW_VIF_IP] = \
                          config[ConfigClassParameter.GUEST_NW_VIF_IP]
                overrides[ConfigClassParameter.GUEST_NW_VIF_NETMASK] = \
                          config[ConfigClassParameter.GUEST_NW_VIF_NETMASK]
        return overrides

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Network___add_workers(self, node_fqdns, config):
        """
        (*)
        This starts the network worker role on the specified nodes, and uses
        the given configuration to configure those nodes. The following
        services are started on the specified nodes:

        *openstack-nova-network*

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Currently there are the following supported configuration settings:

        *MODE*
            Specifies the Network mode for the nodes being added, and
            thus the whole cloud.

            Possible values: flat|vlan (default: flat)

            Note: changing this setting after adding networks may corrupt the
            compute database

        If you have the vlan mode you have the following required settings:

        *GUEST_NETWORK_BRIDGE*
            Specifiy the XenServer network to be used for instance networking.
            e.g. xenbr1

        *BRIDGE_INTERFACE*
            Specify which interface on the network node should be attached
            to GUEST_NETWORK_BRIDGE. This parameter defines the device id of
            the corresponding VIF (e.g.: eth2 -> device = 2).

        *GUEST_NW_VIF_MODE*
            Specify what ip configuration is being used on the VIF
            corresponding to BRIDGE_INTERFACE on the network node

            Possible values: dhcp|static|noip

        if you have vlan or flat dhcp and using static networking,
        you must specifiy:

        *GUEST_NW_VIF_IP*
            IP address for BRIDGE_INTERFACE (e.g. 192.168.1.13)

        *GUEST_NW_VIF_NETMASK*
            The netmast for BRIDGE_INTERFACE (e.g. 255.255.255.0)
        """
        # TODO - validation
        # TODO - detect which hypervisor the specific node is using
        # See how this interacts with publish service
        # Retrieve user selection for MULTI_HOST networking
        # Not finding MULTI_HOST is tantamount to disabling it
        multi_host = config.get("MULTI_HOST", False)
        mode = config["MODE"]
        final_global_config = self._get_network_mode_config(mode, config)
        final_global_config[ConfigClassParameter.MULTI_HOST] = str(multi_host)
        for param_label, value in final_global_config.iteritems():
            self.Config___set(param_label, value)

        # If multi_host has been disabled, do the procedure for unconfiguring
        # ha networking and continue. Otherwise stop, as we should not be here.
        if not multi_host:
            self.Network___configure_ha(config)
        else:
            raise Exception("Should not invoke Network.add_worker"
                            " with MULTI_HOST enabled")

        node_overrides = self._prepare_overrides(mode, config)

        # When assigning the nova-network role to a node, we must ensure
        # PUBLIC_INTERFACE and BRIDGE_INTERFACE have different values, as
        # this role usually has both guest and public VIF config roles.

        # If BRIDGE_INTERFACE has not been overriden, use the global one.
        bridge_if = node_overrides.get(ConfigClassParameter.BRIDGE_INTERFACE,
                                       self.Config___get(
                                            ConfigClassParameter.
                                            BRIDGE_INTERFACE))
        public_if = self.Config___get(ConfigClassParameter.PUBLIC_INTERFACE)
        if bridge_if == public_if:
            #assuming bridge_if is ethX => public_if ethY where Y=X+1
            try:
                dev_no = int(public_if[3:])
                public_if = public_if[:3] + str(dev_no + 1)
            except ValueError:
                pass  # Assumption on ethX was wrong...
            # add node override for public iface
            node_overrides[ConfigClassParameter.PUBLIC_INTERFACE] = public_if

        roles = [Role.NOVA_NETWORK]
        for node_fqdn in node_fqdns:
            model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)
            for param_label, value in node_overrides.iteritems():
                self.Config___add_node_override(node_fqdn, param_label, value)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': roles}

    def Network___delete_workers(self, node_fqdns):
        """Remove workers from the Network fabric. As a result, services
        running on the node (because of a previous add_workers call) stop,
        and the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def Network___update_worker(self, node_fqdn, config):
        """This updates the configuration for the network worker running on
        the specified nodes.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        For supported configuration values, see Network.add_workers.
        """
        raise NotImplemented()

    def Network___configure_ha(self, config):
        """
        (*)
        This API call sets up HA networking configuration according to to the
        values specified in the 'config' parameter.

        When this setting is enabled, each time a compute worker is
        configured, both the nova-network and the nova-compute service
        are started on the worker itself.

        This operation does not assign any role to any node. Therefore it
        does not start any service.

        Currently there are the following supported configuration settings:

        *MULTI_HOST*
            This enables nova HA networking support.
            This parameter must be present in the 'config' dictionary.
            If not present, this operation returns without performing any
            configuration change.
            If True it enables HA networking mode, a redundant configuration
            in which each compute worker also runs the network service.
            If False, HA networking mode is disable, and the nova-network
            service is shut down on each compute host.

            NOTE: Turning on/off HA networking mode when network workers
            are already configured and/or there are instance running, might
            compromise networking in the cloud deployment.

            Possible values: true| false.
        *MODE*
            Specifies the Network mode for the nodes being added, and
            thus the whole cloud.

            Possible values: flat| flatdchp| vlan (default: flat)

            Note: changing this setting after adding networks may corrupt the
            nova database

        If you selected the vlan or the flatdhcp mode you have the
        following required settings:

        *GUEST_NETWORK_BRIDGE*
            Specifiy the XenServer network to be used for instance networking.
            e.g. xenbr1

        *BRIDGE_INTERFACE*
            Specify which interface on the network node should be attached
            to GUEST_NETWORK_BRIDGE. This parameter defines the device id of
            the corresponding VIF (e.g.: eth2 -> device = 2).

        *GUEST_NW_VIF_MODE*
            Specify what ip configuration is being used on the VIF
            corresponding to BRIDGE_INTERFACE on the network node

            Possible values: dhcp|static|noip

        """
        multi_host = config.get("MULTI_HOST", None)
        if multi_host is None:
            return

        mode = config["MODE"]
        final_global_config = self._get_network_mode_config(mode, config)

        final_global_config[ConfigClassParameter.MULTI_HOST] = str(multi_host)
        for param_label, value in final_global_config.iteritems():
            self.Config___set(param_label, value)

        #Disable HA networking
        if not multi_host:
            # Remove the network role from nodes in the group override
            if self.Config___has_override_group(GroupOverride.NETWORK_WORKERS):
                # TODO: must remove the role from the node
                # to do so, we should implement Network___remove_worker
                # Destroy the group override
                self.Config___delete_override_group(
                     GroupOverride.NETWORK_WORKERS)
            return

        # Enable HA networking
        # If MULTI_HOST has been chosen we create a GroupOverride for
        # GUEST_NETWORK_BRIDGE and GUEST_NW_VIF_MODE
        # PUBLIC_BRIDGE will also be overriden if its global value conflicts
        # with BRIDGE_INTERFACE
        # Note: GUEST_NW_VIF_IP and GUEST_NW_VIF_NETMASK must
        # be per-node overrides.
        group_overrides = self._prepare_overrides(mode, config)
        bridge_if = self.Config___get(ConfigClassParameter.BRIDGE_INTERFACE)
        public_if = self.Config___get(ConfigClassParameter.PUBLIC_INTERFACE)
        if bridge_if == public_if:
            #assuming bridge_if is ethX => public_if ethY where Y=X+1
            try:
                dev_no = int(public_if[3:])
                public_if = public_if[:3] + str(dev_no + 1)
            except ValueError:
                pass  # Assumption on ethX was wrong...
            # add override for public iface
            group_overrides[ConfigClassParameter.PUBLIC_INTERFACE] = public_if

        if not self.Config___has_override_group(
                    GroupOverride.NETWORK_WORKERS):
            self.Config___create_override_group(
                 GroupOverride.NETWORK_WORKERS)
        for param_label, value in group_overrides.iteritems():
            self.Config___add_group_override(GroupOverride.NETWORK_WORKERS,
                                             param_label, value)
        #TODO: Must reconfigure workers user migth have already configured
        #Nothing else to do!
        return

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def BlockStorage___add_workers(self, node_fqdns, config):
        """
        (*)
        Adds the block Storage worker role to the specified node_fqdns.
        This involves adding the following roles:

        *openstack-nova-volume*

        node_fqdns(string): the nodes
        config(dict): the configuration
        return(string): the task id

        The following supported config values:

        *TYPE*
            Suppored values: 'iscsi'|'xenserver_sm'
            Currently we only support one type per zone

        When in 'iscsi' mode you must specify:

        *VOLUME_DISK_SIZE_GB*
            Size of the disk (int) that will be added to hold the volumes that
            are later attached to the VMs
        """
        #TODO - validation and extra unit tests required
        # ensure only one node, or only one type per zone
        # ensure corrent things are in the config collections
        stored_config_options = {
            "iscsi": {
                       ConfigClassParameter.VOLUME_DRIVER:
                          "nova.volume.driver.ISCSIDriver",
                       ConfigClassParameter.USE_LOCAL_VOLUMES:
                          "True"},
            "xenserver_sm":
                      {
                       ConfigClassParameter.VOLUME_DRIVER:
                          "nova.volume.xensm.XenSMDriver",
                       ConfigClassParameter.USE_LOCAL_VOLUMES:
                          "False"},
            }

        type = config["TYPE"]

        final_config = stored_config_options[type]

        if type == "iscsi":
            final_config[ConfigClassParameter.VOLUME_DISK_SIZE_GB] = \
                config[ConfigClassParameter.VOLUME_DISK_SIZE_GB]

        for param_label, value in final_config.iteritems():
            self.Config___set(param_label, value)
        # TODO - we should restart any compute nodes, due to volume driver

        # must assign config flags before starting any services
        roles = [Role.NOVA_VOLUME]
        for node_fqdn in node_fqdns:
            model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)

        return {'node_fqdns': node_fqdns,
                'config_params': config.keys(),
                'roles': roles}

    def BlockStorage___delete_workers(self, node_fqdns):
        """Remove workers from the Block Storage fabric. As a result, services
        running on the node (because of a previous add_workers call) stop,
        and the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def BlockStorage___update_worker(self, node_fqdn, config):
        """Configures the block Storage worker role on the specified nodes.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Currently supported configuration values:

        *VOLUME_DISK_SIZE_GB*
            Size of the disk (int). The disk will be resized to the specified
            size
        """
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Imaging___add_registry(self, node_fqdn, config):
        """
        (*)
        Deployes the Image Registry on the specified node. It will
        deploy the following roles:

        *openstack-glance-registry*

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        There are the following supported configuration values:

        *GLANCE_STORE*
            Specifies the supported
            Supported values: swift|file

        if GLACE_STORE=swift you must specifiy:

        *GLANCE_SWIFT_ADDRESS*
            The hostname of the swift auth server

        if GLACE_STORE=file you must specifiy:

        *GLANCE_FILE_STORE_SIZE_GB*
            The size of the disk to attach to store the images.
            Takes an integer, and the size is specified in GB.
        """
        # TODO - need validation
        # TODO - would be nice to fill in swift address automagically
        # TODO - this currently deploys both the API and Regsitry together...
        for param_label, value in config.iteritems():
            self.Config___add_node_override(node_fqdn, param_label, value)

        roles = [Role.GLANCE_API, Role.GLANCE_REGISTRY]
        model_utils.assign_and_configure_roles_to_node(node_fqdn, roles)

        # TODO - this only works with a single node
        self.Config___set(ConfigClassParameter.GLANCE_HOSTNAME, node_fqdn)

        return {'node_fqdns': [node_fqdn],
                'config_params': config.keys(),
                'roles': roles}

    def Imaging___delete_registry(self, node_fqdn):
        """Remove registry from the Imaging System. As a result, services
        running on the node (because of a previous add_workers call) stop,
        and the configuration is cleaned-up.

        node_fqdn(string): the registry node to be removed
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def Imaging___update_registry(self, node_fqdn, config):
        """Update the settings for the registry service on the specified nodes

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Currently supported configurations:

        if GLACE_STORE=swift you can specifiy:

        *GLANCE_SWIFT_ADDRESS*
            The hostname of the swift auth server

        if GLACE_STORE=file you can specifiy:

        *GLANCE_FILE_STORE_SIZE_GB*
            The size of the disk to attach to store the images.
            Takes an integer, and the size is specified in GB.
            The disk will be resized to the values you specify
        """
        raise NotImplemented()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Imaging___add_container(self, node_fqdn, config):
        """This API is added to create image containers on a node. It
        will be deprecated when the upload of VM images will occurred
        using via Glance streaming."""
        roles = [Role.IMG_CONTAINER]
        model_utils.assign_and_configure_roles_to_node(node_fqdn,
                                                       roles,
                                                       config)
        return {'node_fqdns': [node_fqdn],
                'config_params': config.keys(),
                'roles': roles}

    def Imaging___add_apis(self, node_fqdns, config):
        """This makes the specified nodes into Imaging Service API nodes.
        It is good to add API nodes to add extra read capacity to the system.
        It will connect to the exisiting image registry services.
        It will add the following role:

        *openstack-glance-api*

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        There are currently no supported configuration values.
         """
        raise NotImplemented()

    def Imaging___delete_apis(self, node_fqdns):
        """Remove API endpoints from the Imaging System. As a result, services
        running on the node (because of a previous add_workers call) stop, and
        the configuration is cleaned-up.

        node_fqdns(strings): list of nodes to be removed from fabric
        return(string): the uuid of the task operation
        """
        raise NotImplementedError()

    def Imaging___update_api(self, node_fqdn, config):
        """Updates the configration for the imaging api service on the
        specified node.

        node_fqdn(string): the node
        config(dict): the configuration
        return(string): the task id

        Currently there are no supported configuration values.
        """
        raise NotImplementedError()

    def Imaging___add_database(self, node_fqdn, config):
        """Not yet implemented - currently shares the compute database"""
        raise NotImplementedError()

    def Imaging___delete_database(self, node_fqdn):
        """Not yet implemented - currently shares the compute database"""
        raise NotImplementedError()

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def LBaaS___add_api(self, node_fqdn, config):
        """This enable LBaaS demo on an Olympus VPX deployment"""
        roles = [Role.LBSERVICE]
        model_utils.assign_and_configure_roles_to_node(node_fqdn,
                                                       roles,
                                                       config)
        return {'node_fqdns': [node_fqdn],
                'config_params': config.keys(),
                'roles': roles}

    @trace
    @validators.xmlrpc_fault_wrapper
    @task_utils.puppet_kick
    def Task___apply_changes(self, node_fqdns, dont_wait=False):
        """
        (*)
        Attempts to enforce the current configuration on the specified node.

        node_fqdns(list(string)): fqdn of the nodes
        dont_wait(boolean): if True, does not return a task id
        return(string): the task id"""
        return {'node_fqdns': node_fqdns,
                'dont_wait': dont_wait}

    @trace
    @validators.xmlrpc_fault_wrapper
    def Task___get_status(self, task_uuid):
        """
        (*)
        Get the status of the task specified.

        task_uuid(string): the uuid of the task, e.g. '1234-456-...'
        return(string): Possible values includes:

        *PENDING*
        The task is waiting for execution.

        *STARTED*
        The task has been started.
        TODO - Only when this is enabled in celery, which it currently is not

        *RETRY*
        The task is to be retried, possibly because of failure.

        *FAILURE*
        The task raised an exception, or has exceeded the retry limit.
        The :attr:`result` attribute then contains the
        exception raised by the task.

        *SUCCESS*
        The task executed successfully. The :attr:`result` attribute
        then contains the tasks return value."""
        task_result = task_utils.get_task(task_uuid)
        return task_result.state

    @trace
    @validators.xmlrpc_fault_wrapper
    def Task___get_details(self, task_uuids):
        """
        (*)
        Get details about the specified tasks.

        task_uuid(list(string)): the uuids of the tasks
        return: a dictionary that contains details about the tasks e.g.

        Example dictionary for details is:

        { '37b18811-434f-45f8-ae6c-2f1d6c7704fc': { 'status': 'FAILURE',
          'result': 'Exception("Timed out waiting for service to start",)',
          ...,},
        }
        """
        return dict([(x, task_utils.get_task_details(x)) for x in task_uuids])

    @trace
    @validators.xmlrpc_fault_wrapper
    def Task___get_all(self):
        """
        (*)
        Get details about registered task.

        return: dict of dict

        Example dictionary for details is:

        { '37b18811-434f-45f8-ae6c-2f1d6c7704fc': {'status': 'FAILURE',
          'result': 'Exception("Timed out waiting for service to start",)'},
          ...,}
        """
        return task_utils.get_uuids()

    @trace
    @validators.xmlrpc_fault_wrapper
    def Task___get_by_tags(self, tags):
        """
        (*)
        Get a list of any task_ids associated with all of the specified
        tags.

        tags: list of tags e.g. ['tag1', 'tag2', ...]
        returns(list(strings): the task uuids

        Example returned list is:

        ['1234-5678-...', '2345-6789-...']
        """
        return task_utils.get_task_ids_by_tags(tags)

    @trace
    @validators.xmlrpc_fault_wrapper
    def Task___get_all_tags(self):
        """
        (*)
        Get a list of all the task tags.

        return(list(string): the tags defined in the system

        Example list of tags can be:

        ['tag1','tag2',...]
        """
        roles = [role for role in Role.get_service_roles()]
        params = ConfigClassParameter.get_names()
        node_fqdns = Node.get_fqdns()

        return roles + params + node_fqdns

    @trace
    @validators.xmlrpc_fault_wrapper
    def Logger___log(self, level, message):
        """
        (*)
        Log a message at the specified level.

        level(string): DEBUG, INFO, WARNING or ERROR
        message(string): the message that is logged"""
        logger.log(level, message)


svc = GenerateDjangoXMLRPCHandler2(Service(logger))
