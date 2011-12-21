import logging
import stubout
import time
import datetime

from django.test import TestCase
from djcelery.models import TaskState

from geppetto.core.models import Group
from geppetto.core.models import Node
from geppetto.core.models import Master
from geppetto.core.models import Override
from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Role
from geppetto.core.models import NodeRoleAssignment
from geppetto.tasks.node_state import TASK_MONITOR_NAME

logger = logging.getLogger('geppetto.core.tests.test_base')


class DBTestBase(TestCase):

    def setUp(self):
        super(DBTestBase, self).setUp()
        self.dummy_node_fqdn = None
        self.stubs = stubout.StubOutForTesting()
        _add_base_stubout(self.stubs)

    def tearDown(self):
        super(DBTestBase, self).tearDown()
        if self.dummy_node_fqdn != None:
            for node in Node.objects.all():
                node.delete()
            self.dummy_node_fqdn = None
        for group in Group.objects.all():
            group.delete()
        for override in Override.objects.all():
            override.delete()
        self.dummy_taskstate_id = None
        for taskstate in TaskState.objects.all():
            taskstate.delete()
        self.stubs.UnsetAll()

    def _add_dummy_node(self, fqdn='test_fqdn', is_enabled=True):
        self.dummy_node_fqdn = fqdn
        node = Node.create(fqdn)
        node.enabled = is_enabled
        import pickle
        node.facts = pickle.dumps({"geppetto_status_running_services":
                                   "openstack-nova-api,openstack-nova-compute",
                                   "geppetto_status_stopped_services":
                                        "openstack-nova-network",
                                    "host_fqdn": "test_host",
                                    "ipaddress_eth0": "169.254.0.2",
                                    "ipaddress_eth1": "127.0.0.1",
                                    "interfaces": "'eth0,eth1,eth2,lo'", })
        node.save()
        node.joined_date = datetime.datetime(2001, 1, 1, 0, 0, 0, 0)

        # make the host guid predictable
        param = ConfigClassParameter.get_by_name(
                                            ConfigClassParameter.HOST_GUID)
        Override.update_or_create_override(node, param, "00:00:00:00:00:00")

        return node

    def _add_dummy_taskstate(self, id='12345', tags={}):
        self.dummy_taskstate_id = id
        TaskState.objects.create(task_id=id,
                            kwargs="{'tags':%s}" % tags,
                            tstamp=datetime.datetime.now(),
                            name=TASK_MONITOR_NAME)

    def _get_dummy_taskstate(self):
        if not self.dummy_taskstate_id:
            return None
        return TaskState.objects.get(task_id=self.dummy_taskstate_id)

    def _add_blank_node(self, node_fqdn='test_fqdn'):
        node = Node(fqdn=node_fqdn, master=Master.objects.all()[0])
        node.save()
        return node

    def _add_blank_group(self, group_name='test_group'):
        group = Group(name=group_name)
        group.save()
        return group

    def _get_dummy_node(self):
        return Node.objects.get(fqdn=self.dummy_node_fqdn)

    def _add_dummy_override(self,
                            fqdn='test_fqdn',
                            config="VPX_DESCRIPTION",
                            value="test"):
        self._add_dummy_node(fqdn)
        node = self._get_dummy_node()
        config_class_parameter = ConfigClassParameter.get_by_name(config)
        Override.objects.create(node=node,
                                config_class_parameter=config_class_parameter,
                                value=value)

    def _add_dummy_node_into_role(self, fqdn='test_fqdn',
                                  roles=["openstack-dashboard"],
                                  is_enabled=True,):
        node = self._add_dummy_node(fqdn, is_enabled)
        for role in roles:
            r = Role.get_by_name(role)
            NodeRoleAssignment.objects.create(node=node, role=r)
        return node


def _add_base_stubout(stubs):

    def fake_sleep(seconds):
        logger.debug('fake_sleep for %s' % seconds)
    stubs.Set(time, 'sleep', fake_sleep)
