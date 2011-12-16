import logging
import stubout
import string
import datetime

from geppetto.tests import test_base
from geppetto.core.models import utils
from geppetto.core.models.roledependencies import DEFAULT_ROLES
from geppetto.core.models.infrastructure import ReportStatus
from geppetto.core.views.geppetto_service import Service as GService
from geppetto.tests.test_geppetto_api import _add_stubout

logger = logging.getLogger('geppetto.core.tests.classifier_api')


class TestClassifierServiceAPI(test_base.DBTestBase):

    def setUp(self):
        super(TestClassifierServiceAPI, self).setUp()
        self.stubs = stubout.StubOutForTesting()
        _add_stubout(self.stubs)
        with open('tests/fakes/classifier_yaml.test', 'r') as f:
                self.expected_yaml = f.read()

        self.geppetto_svc = GService(logger)
        # import here to stop db errors when importing this test before
        # the db has been created
        from geppetto.core.views.classifier_service import Service as CService
        self.classifier_svc = CService()

    def tearDown(self):
        super(TestClassifierServiceAPI, self).tearDown()
        self.stubs.UnsetAll()

    def test_get_default_configuration(self):
        def _fake_generate_host_guid():
            return "00:00:00:00:be:ef"
        self.stubs.Set(utils, '_generate_host_guid', _fake_generate_host_guid)

        node_name = 'default_node'
        yaml = self.classifier_svc.get_configuration(node_name)
        self.maxDiff = None
        self.assertMultiLineEqual(yaml, self.expected_yaml)

        # test the path when node has already been added
        yaml2 = self.classifier_svc.get_configuration(node_name)
        self.assertMultiLineEqual(yaml2, self.expected_yaml)

    def test_restart_services_due_to_node_copy(self):
        self._add_dummy_node_into_role('keystone1', DEFAULT_ROLES)
        self._add_dummy_node_into_role('keystone2', DEFAULT_ROLES)
        self._add_dummy_node_into_role('swift-proxy', DEFAULT_ROLES)
        self.geppetto_svc.Identity___add_auth('keystone1', {})
        self.geppetto_svc.ObjectStorage___add_apis(['swift-proxy'], {})
        self.geppetto_svc.Node___copy('keystone1', 'keystone2')

        # ensure the correct values are returned
        yaml = self.classifier_svc.get_configuration("swift-proxy")
        self.assertNotEqual(-1, string.find(yaml,
                            "VPX_RESTART_SERVICES: ['openstack-swift-proxy']"))

    def test_restart_services_due_to_node_copy_onetime(self):
        self._add_dummy_node_into_role('node1', DEFAULT_ROLES)
        self._add_dummy_node_into_role('node2', DEFAULT_ROLES)
        node = self._add_dummy_node_into_role('node3', DEFAULT_ROLES)
        self.geppetto_svc.Identity___add_auth('node1', {})
        self.geppetto_svc.ObjectStorage___add_apis(['node3'], {})
        self.geppetto_svc.Node___copy('node1', 'node2')

        node.report_status = ReportStatus.Changed
        node.report_date = datetime.datetime.now()
        node.report_last_changed_date = datetime.datetime.now()
        node.save()
        yaml = self.classifier_svc.get_configuration("node3")
        # test that the override has NOT got away yet
        self.assertNotEqual(-1, string.find(yaml,
                            "VPX_RESTART_SERVICES: ['openstack-swift-proxy']"))
        yaml = self.classifier_svc.get_configuration("node3")
        # test that the override has got away yet
        self.assertEqual(-1, string.find(yaml,
                         "VPX_RESTART_SERVICES: ['openstack-swift-proxy']"))
