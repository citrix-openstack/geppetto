import datetime
import logging

from geppetto.tests import test_base
from geppetto.core import Failure
from geppetto.core.models import utils
from geppetto.core.models import ConfigClassParameter as config
from geppetto.core.models import Group
from geppetto.core.models import GroupOverride
from geppetto.core.models import Master
from geppetto.core.models import Node
from geppetto.core.models import NodeRoleAssignment
from geppetto.core.models import Override
from geppetto.core.models import Role
from geppetto.core.models import RoleDescription
from geppetto.core.models import RoleDesConfigParamAssignment

from geppetto.core.models.roledependencies import DEFAULT_ROLES

logger = logging.getLogger('geppetto.core.tests.geppetto_model')


class TestGeppettoModel(test_base.DBTestBase):

    def setUp(self):
        super(TestGeppettoModel, self).setUp()

    def tearDown(self):
        super(TestGeppettoModel, self).tearDown()

    def test_master_promote(self):
        Master.promote_node('master.openstack.org')
        m = Master.objects.get(fqdn='master.openstack.org')
        self.assertEqual(m.fqdn, 'master.openstack.org')

    def test_get_overrides(self):
        node = self._add_blank_node()
        d1 = {config.HAPI_USER: 'bob',
              config.HAPI_PASS: 'ciao',
              config.MYSQL_USER: 'bob2',
              config.MYSQL_PASS: 'ciao2', }
        for key, value in d1.iteritems():
            Override.update_or_create_override(node,
                                               config.get_by_name(key),
                                               value)
        d2 = node.get_overrides_dict()
        self.assertDictEqual(d1, d2)

    def test_get_group_overrides(self):
        node = self._add_blank_node()
        group = self._add_blank_group('password_group')
        node.update_group(group)
        d1 = {config.HAPI_USER: 'bob',
              config.HAPI_PASS: 'ciao',
              config.MYSQL_USER: 'bob2',
              config.MYSQL_PASS: 'ciao2', }
        for key, value in d1.iteritems():
            GroupOverride.create(group, key, value)
        d2 = node.get_group_overrides_dict()
        self.assertDictEqual(d1, d2)

    def test_config_get_all(self):
        configs = config.get_values()
        self.assertGreater(len(configs), 0, '')

    def test_get_service_roles(self):
        roles = Role.get_service_roles()
        self.assertGreater(len(roles), 0)

    def test_group_create(self):
        try:
            Group.create('fake_group')
        except:
            self.fail('This should not have failed')

    def test_group_create_raise_exception(self):
        try:
            Group.create('fake_group')
            Group.create('fake_group')
            self.fail()
        except:
            pass

    def test_group_delete(self):
        try:
            Group.create('fake_group1')
            Group.delete_by_name('fake_group1')
        except:
            self.fail('This should not have failed')

    def test_group_delete_raise_exception(self):
        try:
            Group.delete_by_name('fake_group2')
            self.fail()
        except:
            pass

    def test_config_set_raise_exception(self):

        def _test_method_assert_raise(testrunner, *args):
            testrunner.assertRaises(Failure,
                                    config.set_config_parameter,
                                    *args)

        invalid_params = {'VMWAREAPI_WSDL_LOC':
                            'file:///etc/openstack/visdk/vimService.wsdl',
                          'NS_VPX_VM_MAC_ADDRESS': 'AA:BB:CC:DD:EE',
                          'API_BIND_HOST': '127.0.0',
                          'API_BIND_PORT': 700000,
                          'DASHBOARD_SMTP_USR': 'wrong@email',
                          'SWIFT_PROXY_ADDRESS': 'localhost$', }

        for param_name, param_value in invalid_params.iteritems():
            _test_method_assert_raise(self, param_name, param_value)

    def test_config_set_success(self):

        def _test_method_assert_equal(testrunner, name, value):
            config.set_config_parameter(name, value)
            self.assertEqual(value, config.get_value_by_name(name))

        valid_params = {'API_BIND_PORT': '1024',
                        'SWIFT_PROXY_ADDRESS': 'fqdn1.example.org',
                        'DASHBOARD_SMTP_USR': 'admin@example.org', }

        for param_name, param_value in valid_params.iteritems():
            _test_method_assert_equal(self, param_name, param_value)

    def test_configs_get_by_role(self):
        role = Role.get_by_name('openstack-glance-api')
        configs = role.get_config_labels()
        logger.debug(configs)
        self.assertGreater(len(configs), 1)

    def test_get_node_details(self):
        node = self._add_dummy_node()
        details = node.get_details()
        valid_details = {'fqdn': 'test_fqdn',
                         'group_id': None,
                         'group_overrides': {},
                         'host_fqdn': 'test_host',
                         'host_id': None,
                         'host_ipaddress': 'N/A',
                         'host_virt': 'N/A',
                         'interfaces': "'eth0,eth1,eth2,lo'",
                         'id': 1,
                         'joined_date': datetime.datetime(2001, 1, 1, 0, 0),
                         'management_ip': '127.0.0.1',
                         'hostnetwork_ip': '169.254.0.2',
                         'master_id': 1,
                         'master_fqdn': u'master',
                         'node_overrides': {"HOST_GUID": "00:00:00:00:00:00"},
                         'report_date': None,
                         'report_last_changed_date': None,
                         'report_status': '',
                         'roles': []}
        self.maxDiff = None
        self.assertDictEqual(valid_details, details)

    def test_default_role(self):
        roles1 = [r.name for r in Role.objects.filter(name__in=DEFAULT_ROLES)]
        roles2 = []
        for rolename in DEFAULT_ROLES:
            roles2.append(Role.objects.get(name=rolename).name)
        roles1.sort()
        roles2.sort()
        self.assertListEqual(roles1, roles2)

    def test_copy_role_assignements(self):
        node_src = self._add_dummy_node('node_src')
        node_dst = self._add_dummy_node('node_dst')
        role_assignments = \
              [NodeRoleAssignment.\
               objects.create(node=node_src,
                              role=Role.get_by_name('openstack-nova-compute'),
                              enabled=True),
               NodeRoleAssignment.\
               objects.create(node=node_src,
                              role=Role.get_by_name('openstack-nova-api'),
                              enabled=True), ]
        NodeRoleAssignment.copy_role_assignments_to_node(role_assignments,
                                                         node_dst)
        self.assertListEqual(node_src.get_roles(), node_dst.get_roles())

    def test_update_related_config_params(self):
        keystone_roles = [Role.KEYSTONE_AUTH,
                          Role.KEYSTONE_ADMIN]
        keystone_roles.extend(DEFAULT_ROLES)
        ks1 = self._add_dummy_node_into_role('ks1', keystone_roles)
        ks2 = self._add_dummy_node_into_role('ks2', DEFAULT_ROLES)
        self._add_dummy_node_into_role('client-vpx', DEFAULT_ROLES)

        roles = NodeRoleAssignment.\
            copy_role_assignments_to_node(ks1.get_role_assignments(), ks2)
        node_fqdns = utils.update_related_config_params(roles, 'ks2')
        self.assertIn('client-vpx', node_fqdns)

    def test_copy_node_overrides(self):
        node_src = self._add_dummy_node('node_src')
        node_dst = self._add_dummy_node('node_dst')
        c1 = config.get_by_name('HAPI_PASS')
        c2 = config.get_by_name('HAPI_USER')
        overrides = \
            [Override.\
             objects.create(node=node_src,
                            config_class_parameter=c1,
                            value='mysecret'),
             Override.\
             objects.create(node=node_src,
                            config_class_parameter=c2,
                            value='myuser'), ]
        Override.copy_node_overrides(node_dst, overrides)
        self.assertDictEqual(node_dst.get_overrides_dict(),
                         node_src.get_overrides_dict())

    def test_delete_overrides(self):
        self._add_dummy_override('node_1234')
        node = Node.get_by_name('node_1234')
        node.delete_overrides()
        overrides = node.get_overrides_dict()
        self.assertDictEqual({}, overrides)

    def test_delete_roles(self):
        nova_api = RoleDescription.get_by_name('OpenStack Compute API')
        composition = nova_api.get_composition()
        self._add_dummy_node_into_role('node_1234',
                                       composition + DEFAULT_ROLES)
        node = Node.get_by_name('node_1234')
        node.delete_roles()
        roles = [r.name for r in node.get_roles()]
        self.assertListEqual(DEFAULT_ROLES, roles)

    def test_get_role_dict(self):
        roles = Role.get_roles_dict()
        self.assertEquals(roles['openstack-nova-api'],
                          'OpenStack Compute API')

    def test_get_role_compositions(self):
        compositions = RoleDescription.get_compositions()
        self.assertListEqual(compositions['OpenStack Compute Worker'],
                             ['openstack-nova-compute'])

    def test_get_fqdns_by_roles(self):
        nova_api = RoleDescription.get_by_name('OpenStack Compute API')
        composition = nova_api.get_composition()
        node = self._add_dummy_node_into_role('node_1234', composition)
        nodes = Node.get_fqdns_by_roles(composition)
        self.assertEqual(node.fqdn, nodes[0])
        self.assertEqual(len(nodes), 1)

    def test_get_configparam_by_role_description(self):
        params = RoleDesConfigParamAssignment.\
                    get_param_labels_by_description('OpenStack Compute API')
        expected_params = ['COMPUTE_API_HOST']
        self.assertListEqual(expected_params, params)

    def test_get_fqdns_exclude_by_roles(self):
        self._add_dummy_node_into_role('test1', [Role.OPENSTACK_DASHBOARD,
                                                 Role.NOVA_API])
        self._add_dummy_node_into_role('test2', [Role.NOVA_COMPUTE,
                                                 Role.NOVA_NETWORK])
        self._add_dummy_node_into_role('test3', [Role.SWIFT_ACCOUNT,
                                                 Role.SWIFT_OBJECT])
        node_fqdns = Node.get_fqdns_excluded_by_roles([Role.NOVA_COMPUTE])
        self.assertListEqual(['test1', 'test3'], node_fqdns)
