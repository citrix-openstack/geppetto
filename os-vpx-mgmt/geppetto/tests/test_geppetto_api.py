import logging
import socket
import xmlrpclib
import stubout

from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import GroupOverride
from geppetto.core.models import Role
from geppetto.tasks import node_state
from geppetto.geppettolib import puppet
from geppetto.geppettolib import network
from geppetto.tests import test_base

from geppetto.core.views import geppetto_service
from geppetto.core.models.roledependencies import DEFAULT_ROLES

logger = logging.getLogger('geppetto.core.tests.geppetto_api')


class TestGeppettoServiceAPI(test_base.DBTestBase):

    def setUp(self):
        super(test_base.DBTestBase, self).setUp()
        self.stubs = stubout.StubOutForTesting()
        self.svc = geppetto_service.Service(logger)
        _add_stubout(self.stubs)

    def tearDown(self):
        super(test_base.DBTestBase, self).tearDown()
        self.stubs.UnsetAll()

    def test_config_get(self):
        self.assertEqual(self.svc.Config___get(ConfigClassParameter.HAPI_PASS),
                         ' ')

    def test_config_get_all(self):
        configs = self.svc.Config___get_all()
        # test that the dictionary is return and contains a config
        # like HAPI_PASS
        self.assertIn('HAPI_PASS', configs)

    def test_config_get_details(self):
        details = self.svc.Config___get_details(['RABBIT_HOST'])
        expected = {u'RABBIT_HOST':
                    {'applies-to': [u'openstack-nova-api',
                                    u'openstack-nova-compute',
                                    u'openstack-nova-network',
                                    u'openstack-nova-scheduler',
                                    u'openstack-nova-volume'],
                    'config-description': u"Stores credentials to access "
                    "the message queue in '/etc/openstack/rabbitmq'",
                    'config-name': u'rabbitmq-config',
                    'param-description': u'',
                    'param-description': u'The FQDN of the message queue node',
                    'param-type': u'fqdn',
                    'param-value': u'localhost'}}

        self.maxDiff = None
        self.assertDictEqual(expected, details)

    def test_config_set_param(self):
        config1 = self.svc.Config___get('HAPI_PASS')
        self.svc.Config___set('HAPI_PASS', 'test_password')
        config2 = self.svc.Config___get('HAPI_PASS')
        self.assertNotEqual(config1, config2)

    def test_config_remove_override(self):
        self._add_dummy_node('fake_fqdn')
        self.svc.Config___add_node_override('fake_fqdn',
                                            'HAPI_PASS',
                                            'test')
        self.svc.Config___remove_node_override('fake_fqdn', 'HAPI_PASS')

    def test_config_remove_override_raise_exc(self):
        self._add_dummy_node('fake_fqdn')
        self.assertRaises(xmlrpclib.Fault,
                         self.svc.Config___remove_node_override,
                         'fake_fqdn', 'HAPI_PASS')

    def test_config_get_override_group_details(self):
        group_name = 'fake_override_group'
        group = self._add_blank_group(group_name)
        node1 = self._add_dummy_node('node1')
        node2 = self._add_dummy_node('node2')
        node1.set_group(group)
        node2.set_group(group)
        GroupOverride.create(group, 'HAPI_PASS', 'test_pass')
        GroupOverride.create(group, 'HAPI_USER', 'test_user')
        details1 = {'overrides': {'HAPI_PASS': 'test_pass',
                                  'HAPI_USER': 'test_user', },
                    'nodes': [u'node1', u'node2'], }
        details2 = self.svc.Config___get_override_group_details(group_name)
        self.assertDictEqual(details1, details2)

    def test_Node___get_all(self):
        self._add_dummy_node('fake_fqdn')
        self.assertEqual(self.svc.Node___get_all()[0],
                         'fake_fqdn')

    def test_Node___get_details_ignore_missing_node(self):
        self._add_dummy_node('fake_fqdn1')
        self._add_dummy_node('fake_fqdn2')
        details = self.svc.Node___get_details(['fake_fqdn1',
                                               'fake_fqdn2',
                                               'fake_fqdn3'])
        self.assertListEqual(['fake_fqdn2', 'fake_fqdn1'],
                             details.keys())

    def test_Node___copy(self):
        self._add_dummy_node('node1')
        node2 = self._add_dummy_node('node2')
        self.svc.Compute___add_workers(["node1"], {})

        self.svc.Node___copy("node1", "node2")

        # ensure node2 has the compute role
        role_list = node2.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-compute")],
                            role_list)
        # ensure node1 has been deleted
        self.assertListEqual(["node2"], self.svc.Node___get_all())

    def _Node___copy_util(self, node1, node2, initial_workers, \
                          svc_call, config_dict, config_param_label):
        self._add_dummy_node_into_role(node1, DEFAULT_ROLES)
        self._add_dummy_node_into_role(node2, DEFAULT_ROLES)
        svc_call(initial_workers, config_dict)
        self.svc.Node___copy(node1, node2)
        self.assertEqual(node2, self.svc.Config___get(config_param_label))

    def test_Node___copy_updates_keystone_host(self):
        self._Node___copy_util('node1', 'node2', 'node1', \
                               self.svc.Identity___add_auth, \
                               {}, ConfigClassParameter.KEYSTONE_HOST)

    def test_Node___copy_check_restart_services(self):
        self._add_dummy_node_into_role('keystone1', DEFAULT_ROLES)
        self._add_dummy_node_into_role('keystone2', DEFAULT_ROLES)
        self._add_dummy_node_into_role('swift-proxy', DEFAULT_ROLES)
        self.svc.Identity___add_auth('keystone1', {})
        self.svc.ObjectStorage___add_apis(['swift-proxy'], {})
        self.svc.Node___copy('keystone1', 'keystone2')

        # odd formatting to make new pep8 happy
        node_details = self.svc.Node___get_details(['swift-proxy'])
        overrides = node_details['swift-proxy']['node_overrides']
        swift_restart = overrides[ConfigClassParameter.VPX_RESTART_SERVICES]

        self.maxDiff = None
        self.assertEqual(u"['openstack-swift-proxy']", swift_restart)

    def test_Node___copy_check_restart_services_duplicates(self):
        self._add_dummy_node_into_role('keystone1', DEFAULT_ROLES)
        self._add_dummy_node_into_role('keystone2', DEFAULT_ROLES)
        self._add_dummy_node_into_role('openstack-nova-api', DEFAULT_ROLES)
        self.svc.Identity___add_auth('keystone1', {})
        self.svc.Imaging___add_registry('keystone1', {})
        self.svc.Compute___add_apis(['openstack-nova-api'], {})
        self.svc.Node___copy('keystone1', 'keystone2')

        # odd formatting to make new pep8 happy
        node_details = self.svc.Node___get_details(['openstack-nova-api'])
        overrides = node_details['openstack-nova-api']['node_overrides']
        api_restart = overrides[ConfigClassParameter.VPX_RESTART_SERVICES]

        self.maxDiff = None
        self.assertEqual(u"['openstack-nova-api']", api_restart)

    def test_Node___copy_updates_glance_host(self):
        self._Node___copy_util('node1', 'node2', 'node1', \
                               self.svc.Imaging___add_registry, \
                               {}, ConfigClassParameter.GLANCE_HOSTNAME)

    def test_Node___copy_updates_compute_api_host(self):
                self._Node___copy_util('node1', 'node2', ['node1'], \
                               self.svc.Compute___add_apis, \
                               {}, ConfigClassParameter.COMPUTE_API_HOST)

    def test_get_service_roles(self):
        roles = self.svc.Role___get_service_roles()
        self.assertGreater(len(roles), 0, '')

    def test_role_has_node_is_false(self):
        self.assertFalse(self.svc.Role___has_node('openstack-dashboard'))

    def test_role_has_node_is_true_when_node_in_role(self):
        self._add_dummy_node_into_role('fake_fqdn', ['openstack-dashboard'])
        self.assertTrue(self.svc.Role___has_node('openstack-dashboard'))

    def test_role_has_node_throws_exception_when_wrong_role(self):
        self.assertRaises(xmlrpclib.Fault, self.svc.Role___has_node, 'bob')

    def test_ObjectStore__add_storage_nodes_returns_task_id(self):
        self._add_dummy_node('test1')
        self._add_dummy_node('test2')
        self._add_dummy_node('test3')

        storage_nodes = ["test1", "test2", "test3"]
        config = {ConfigClassParameter.SWIFT_DISK_SIZE_GB: 5}
        self.assertEqual("task_id", self.svc.ObjectStorage___add_workers(
                                                                storage_nodes,
                                                                config))

    def test_ObjectStore__add_storage_nodes_on_duplicate(self):
        self._add_dummy_node('test1')
        self._add_dummy_node('test2')
        self._add_dummy_node('test3')

        storage_nodes = ["test1", "test1", "test3"]
        self.assertRaises(xmlrpclib.Fault,
                          self.svc.ObjectStorage___add_workers,
                          storage_nodes,
                          {})

    def test_ObjectStore__add_apis_throws_on_wrong_node(self):
        self._add_dummy_node('test1')
        self._add_dummy_node('test2')
        self._add_dummy_node('test3')

        self.assertRaises(xmlrpclib.Fault,
                          self.svc.ObjectStorage___add_apis,
                          ['test_asdf'], {})

    def test_ObjectStore__add_storage_nodes_throw_missing_config(self):
        self._add_dummy_node('test1')
        self._add_dummy_node('test2')
        self._add_dummy_node('test3')

        storage_nodes = ["test1", "test2", "test3"]

        self.assertRaises(xmlrpclib.Fault,
                        self.svc.ObjectStorage___add_workers,
                        storage_nodes,
                        {})

    def _test_node_fqdn_and_config_validation(self, method, allow_none=False):
        # test valid fqdn
        self.assertRaises(xmlrpclib.Fault,
                          method, "test1", None)

        self._add_dummy_node('test1')

        if not allow_none:
            self.assertRaises(xmlrpclib.Fault,
                          method, "test1", None)

        self.assertRaises(xmlrpclib.Fault,
                          method,
                          "test1",
                          {"bob": ""})

    def test_Compute___add_database__test_validation(self):
        self._test_node_fqdn_and_config_validation(
                                               self.svc.Compute___add_database)

    def test_Compute___add_database_valid_params_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Compute___add_database("test1",
                                                 {"MYSQL_PASS": "password"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("mysqld")], role_list)

        mysql_pass = ConfigClassParameter.get_by_name("MYSQL_PASS")
        self.assertEqual("password", mysql_pass.default_value)

        mysql_host = ConfigClassParameter.get_by_name("MYSQL_HOST")
        self.assertEqual("test1", mysql_host.default_value)

    def test_Compute___add_message_queue__test_validation(self):
        self._test_node_fqdn_and_config_validation(
                                       self.svc.Compute___add_message_queue,
                                       True)

    def test_Compute___add_message_queue_valid_params_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Compute___add_message_queue("test1")
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("rabbitmq-server")], role_list)

        rabbit_host = ConfigClassParameter.get_by_name("RABBIT_HOST")
        self.assertEqual("test1", rabbit_host.default_value)

    def test_BlockStorage___add_workers_valid_parms_returns_task_id_sm(self):
        self._add_dummy_node('test1')

        result = self.svc.BlockStorage___add_workers(["test1"],
                                                     {"TYPE": "xenserver_sm"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-volume")],
                         role_list)

        volume_driver = ConfigClassParameter.get_by_name("VOLUME_DRIVER")
        self.assertEqual("nova.volume.xensm.XenSMDriver",
                         volume_driver.default_value)

        use_local_volumes = ConfigClassParameter.\
                                get_by_name("USE_LOCAL_VOLUMES")
        self.assertEqual("False", use_local_volumes.default_value)

    def test_BlockStorage___add_workers_valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.BlockStorage___add_workers(["test1"],
                                                  {"TYPE": "iscsi",
                                                   "VOLUME_DISK_SIZE_GB": "5"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-volume")],
                         role_list)

        volume_driver = ConfigClassParameter.get_by_name("VOLUME_DRIVER")
        self.assertEqual("nova.volume.driver.ISCSIDriver",
                         volume_driver.default_value)

        use_local_volumes = ConfigClassParameter.\
                                get_by_name("USE_LOCAL_VOLUMES")
        self.assertEqual("True",
                         use_local_volumes.default_value)

        size = ConfigClassParameter.get_by_name("VOLUME_DISK_SIZE_GB")
        self.assertEqual("5", size.default_value)

    def test_Compute__add_apis_valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Compute___add_apis(["test1"], {})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-api"),
                          Role.get_by_name("openstack-dashboard")],
                         role_list)

        host = ConfigClassParameter.\
                                get_by_name("COMPUTE_API_HOST")
        self.assertEqual("test1",
                         host.default_value)

    def test_Compute__add_worker_valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Compute___add_workers(["test1"], {})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-compute")],
                         role_list)

    def test_Imaging___add_registry_valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Imaging___add_registry("test1",
                                            {"GLANCE_STORE": "file",
                                             "GLANCE_FILE_STORE_SIZE_GB": "5"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-glance-api"),
                          Role.get_by_name("openstack-glance-registry")],
                         role_list)

        overrides = dummy_node.get_overrides_dict()
        self.assertEqual("file", overrides["GLANCE_STORE"])
        self.assertEqual("5", overrides["GLANCE_FILE_STORE_SIZE_GB"])

        host = ConfigClassParameter.\
                                get_by_name("GLANCE_HOSTNAME")
        self.assertEqual("test1",
                         host.default_value)

    def test_Network___add_workers__valid_flatdhcp_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Network___add_workers(["test1"],
                                            {"MODE": "flatdhcp",
                                             "GUEST_NETWORK_BRIDGE": "xenbr1",
                                             "GUEST_NW_VIF_MODE": "noip"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-network")],
                          role_list)

        network_manager = ConfigClassParameter.\
                                get_by_name("NETWORK_MANAGER")
        self.assertEqual("nova.network.manager.FlatDHCPManager",
                         network_manager.default_value)

    def test_Network___add_workers__valid_vlan_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Network___add_workers(["test1"],
                                            {"MODE": "vlan",
                                             "GUEST_NETWORK_BRIDGE": "xenbr1",
                                             "GUEST_NW_VIF_MODE": "static",
                                             "GUEST_NW_VIF_IP":
                                                "192.168.0.200",
                                             "GUEST_NW_VIF_NETMASK":
                                                "255.255.255.0"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-network")],
                          role_list)

        network_manager = ConfigClassParameter.\
                                get_by_name("NETWORK_MANAGER")
        self.assertEqual("nova.network.manager.VlanManager",
                         network_manager.default_value)
        # TODO stub out hpai layer to test other one

        overrides = dummy_node.get_overrides_dict()
        self.assertEqual("static", overrides["GUEST_NW_VIF_MODE"])
        self.assertEqual("192.168.0.200", overrides["GUEST_NW_VIF_IP"])
        self.assertEqual("255.255.255.0", overrides["GUEST_NW_VIF_NETMASK"])

    def test_Network___add_workers__valid_flat_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Network___add_workers(["test1"],
                                            {"MODE": "flat"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-network")],
                          role_list)

        network_manager = ConfigClassParameter.\
                                get_by_name("NETWORK_MANAGER")
        self.assertEqual("nova.network.manager.FlatManager",
                         network_manager.default_value)

    def test_Network___configure_ha_performs_valid_configuration(self):
        self.svc.Network___configure_ha({"MULTI_HOST": True,
                                        "MODE": "flatdhcp",
                                        "GUEST_NETWORK_BRIDGE": "xen_pippo",
                                        "GUEST_NW_VIF_MODE": "noip",
                                        "BRIDGE_INTERFACE": "eth666"})
        # Validate global config
        self.assertEqual(self.svc.Config___get(
                        ConfigClassParameter.MULTI_HOST), "True")
        self.assertEqual(self.svc.Config___get(
                        ConfigClassParameter.NETWORK_MANAGER),
                        "nova.network.manager.FlatDHCPManager")
        # Validate group overrides
        self.assertEqual(self.svc.Config___get_override_group_details(
                         GroupOverride.NETWORK_WORKERS)['overrides'],
                         {"GUEST_NW_VIF_MODE": "noip"})

    def test_Scheduling___add_workers__valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Scheduling___add_workers(["test1"], {})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-nova-scheduler")],
                         role_list)

    def test_ObjectStorage___add_workers__valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.ObjectStorage___add_workers(["test1"],
                                                      {"SWIFT_DISK_SIZE_GB":
                                                                          "5"})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-swift-account"),
                          Role.get_by_name("openstack-swift-container"),
                          Role.get_by_name("openstack-swift-object"),
                          Role.get_by_name("openstack-swift-rsync"),
                          Role.get_by_name("os-vpx-ring-builder")],
                         role_list)

        overrides = dummy_node.get_overrides_dict()
        self.assertEqual("111.111.111.0", overrides["SWIFT_NODES_IPS"])

    def test_ObjectStorage___add_apis__valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.ObjectStorage___add_apis(["test1"], {})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("memcached"),
                          Role.get_by_name("openstack-swift-proxy")],
                         role_list)

        proxy_address = ConfigClassParameter.\
                                    get_by_name("SWIFT_PROXY_ADDRESS")
        self.assertEqual("test1", proxy_address.default_value)

    def test_Identity___add_auth__valid_parms_returns_task_id(self):
        self._add_dummy_node('test1')

        result = self.svc.Identity___add_auth("test1", {})
        self.assertEqual(result, "task_id")

        dummy_node = self._get_dummy_node()
        role_list = dummy_node.get_roles()
        self.assertEqual([Role.get_by_name("openstack-keystone-auth"),
                          Role.get_by_name("openstack-keystone-admin")],
                         role_list)

        hostname = ConfigClassParameter.\
                                    get_by_name("KEYSTONE_HOST")
        self.assertEqual("test1", hostname.default_value)

    def test_Task___get_by_tags__valid_params__finds_task(self):
        self._add_dummy_taskstate("12345", ["bob", "asdf", "asdf1"])
        self._add_dummy_taskstate("23456", ["bob", "asdf"])
        self._add_dummy_taskstate("34567", ["bob"])

        tasks = self.svc.Task___get_by_tags(["asdf", "bob"])

        self.assertEqual(["12345", "23456"], tasks)

    def test_Task___get_by_tags__valid_params__doesnt_find_task(self):
        self._add_dummy_taskstate("12345", ["asdf1"])

        tasks = self.svc.Task___get_by_tags(["asdf2"])

        self.assertEqual([], tasks)

    def test_Task___get_all_tags__returns_correct_list(self):
        self._add_dummy_node('test1')

        tags = self.svc.Task___get_all_tags()

        self.assertTrue('openstack-lb-service' in tags)
        self.assertTrue('COMPUTE_VLAN_INTERFACE' in tags)
        self.assertTrue('test1' in tags)
        self.assertEqual(len(tags), 126)


def _add_stubout(stubs):

    def fake_remote_puppet_run(test_node):
        logger.debug('fake_remote_puppet_run on node %s' % test_node)

    stubs.Set(puppet, 'remote_puppet_run_async', fake_remote_puppet_run)

    def fake_apply_async(*args, **kwargs):
        class fake_task_result():
            def __init__(self, task_id):
                self.task_id = task_id
        return fake_task_result("task_id")

    stubs.Set(node_state.monitor, 'apply_async', fake_apply_async)

    def fake_gethostbyname(hostname):
        return "111.111.111.0"
    stubs.Set(socket, 'gethostbyname', fake_gethostbyname)

    def fake_get_hostname():
        return "test1"
    stubs.Set(network, 'get_hostname', fake_get_hostname)
