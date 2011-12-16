import logging

from django.test import TestCase

from geppetto.hapi import config_util
from geppetto.hapi.interface import Session

logger = logging.getLogger('geppetto.core.tests.geppetto_api')


class TestHAPI(TestCase):

    def setUp(self):
        super(TestHAPI, self).setUp()

    def tearDown(self):
        super(TestHAPI, self).tearDown()

    def test_xapi_sanity(self):
        session = Session.createSession(config_util.HYPERVISOR.XEN_API)
        if session is None:
            self.fail('Unable to load XenAPI session driver')
        # to test hapi locally you can comment out the following two lines
        # and configure:
        #     /etc/openstack/xapi-url
        #     /etc/openstack/hapi
        #else:
        #    session.login()
        #    props = session.VM.get_properties(['memory', 'name'])
        #    logger.debug(props['memory'])
        #    logger.debug(props['name'])

    def test_vmware_sanity(self):
        pass
