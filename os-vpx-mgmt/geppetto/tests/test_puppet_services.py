import datetime
import logging
import stubout

from geppetto.tests import test_base
from geppetto.tests.test_geppetto_api import _add_stubout

from geppetto.core.models import Node

from geppetto.core.views import report_service
from geppetto.core.views import facter_service
from geppetto.core.models.infrastructure import ReportStatus

logger = logging.getLogger('geppetto.core.tests.classifier_api')


class TestPuppetServices(test_base.DBTestBase):

    def setUp(self):
        super(TestPuppetServices, self).setUp()
        self.stubs = stubout.StubOutForTesting()
        _add_stubout(self.stubs)
        with open('tests/fakes/node_report.test', 'r') as f:
            self.raw_post_data = f.read()
        with open('tests/fakes/node_facts.test', 'r') as f:
            self.node_facts = f.read()

    def tearDown(self):
        super(TestPuppetServices, self).tearDown()
        self.stubs.UnsetAll()

    def testSimpleReport(self):
        self._add_dummy_node('test_node')
        report_service.process_report(self)
        node = Node.get_by_name('test_node')
        self.assertEqual(node.report_status, ReportStatus.Changed)
        self.assertEqual(node.report_date, datetime.datetime(2001, 1, 1,
                                                             0, 0, 0, 0))
        self.assertEqual(node.report_log, u'Puppet: FAKE LOG')

    def testSimpleFacts(self):
        self.expected_facts = {'host_fqdn': 'host_fqdn1232131',
                               'host_ip': '10.219.13.20',
                               'host_local_storage_size': 237568532480L,
                               'host_local_storage_utilisation': 4657770496L,
                               'host_memory_free': 22468952064L,
                               'host_memory_total': 25759420416L,
                               'host_password_status': 'SET',
                               'host_type': 'xenapi', }

        self._add_dummy_node('test_node')
        svc = facter_service.Service()
        svc.process_facts('test_node', self.node_facts)
        node = Node.get_by_name('test_node')
        for fact_key, fact_value in self.expected_facts.items():
            self.assertEqual(fact_value, node.get_fact(fact_key))
