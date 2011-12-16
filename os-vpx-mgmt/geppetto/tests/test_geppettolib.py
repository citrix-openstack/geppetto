import commands
import random
import re
import logging

from django.test import TestCase

from geppetto.geppettolib import config_generator
from geppetto.geppettolib.network import NetworkConfiguration, ValidateIP
from geppetto.geppettolib.puppet import PuppetNode, _get_puppet_option

from django.utils import unittest

logger = logging.getLogger('geppetto.core.tests.geppettolib')


class TestGeppettoLib(TestCase):

    def setUp(self):
        super(TestGeppettoLib, self).setUp()
        NetworkConfiguration.IFCFG_FILE = 'tests/fakes/ifcfg-%s.test'
        NetworkConfiguration.NETWK_FILE = 'tests/fakes/net.test'
        NetworkConfiguration.RESLV_FILE = 'tests/fakes/res.test'
        NetworkConfiguration.RESLV_IFACE_FILE = 'tests/fakes/res.%s.test'
        NetworkConfiguration.NTPCF_FILE = 'tests/fakes/ntp.test'
        NetworkConfiguration.HOSTS_FILE = 'tests/fakes/hosts.test'
        NetworkConfiguration.DHCLIENT_FILE = 'tests/fakes/dhclient.test'
        PuppetNode.PCONF_FILE = 'tests/fakes/puppet.test'
        PuppetNode.STATE_FILE = 'tests/fakes/state.test'
        PuppetNode.ASIGN_FILE = 'tests/fakes/asign.test'
        config_generator.TEMPLATES_PATH = 'core/templates'
        self.server = _get_puppet_option(PuppetNode.PCONF_FILE,
                                         'server',
                                         r'[-A-Za-z0-9.]+$')
        self.interval = int(_get_puppet_option(PuppetNode.PCONF_FILE,
                                                  'runinterval',
                                                  r'[0-9]+'))
        with open(PuppetNode.ASIGN_FILE, 'r') as f:
                self.asign = f.read()

    def tearDown(self):
        super(TestGeppettoLib, self).tearDown()
        options = {'client-poll-interval': self.interval,
                   'client-master-reference': self.server, }
        puppet = PuppetNode()
        puppet.set_service_settings(options)
        with open(PuppetNode.ASIGN_FILE, 'w') as f:
                f.write(self.asign)

    def test_network_config(self):
        network = NetworkConfiguration()
        network.load_interface('eth1')
        network.load_network()
        network.load_dns()
        network.load_ntp()
        logger.debug('network.address %s' % network.address)
        logger.debug('network.device %s' % network.device)
        logger.debug('network.bootproto %s' % network.bootproto)
        logger.debug('network.netmask %s' % network.netmask)
        logger.debug('network.gateway %s' % network.gateway)
        logger.debug('network.hostname %s' % network.hostname)
        logger.debug('network.dns_server %s' % network.dns_server)
        logger.debug('network.dns_suffix %s' % network.dns_suffix)
        logger.debug('network.ntp_server %s' % network.ntp_server)
        try:
            # Improve this test coverage
            network.set_interface('eth1',
                                  'static',
                                  '255.255.255.0',
                                  '192.168.1.1')
            network.set_network('dummy-hostname',
                                'mycloud.com',
                                '192.168.1.1')
            network.set_dns_server('192.168.1.1',
                                   'mycloud.com',
                                   '1.168.192')
            network.set_ntp_server('192.168.1.1')
        except Exception, e:
            self.fail('Unexpected exception!')
            logger.exception(e)

    def test_puppet_client_config(self):
        puppet = PuppetNode()
        puppet.load()
        random.seed()
        interval = int(random.uniform(10, 1000))
        fqdn = '%s.mycloud.org' % _generate_word()
        options = {'client-poll-interval': interval,
                   'client-master-reference': fqdn, }
        puppet.set_service_settings(options)
        logger.debug('Am I a master? %s' % puppet.is_master())
        expected = int(_get_puppet_option(PuppetNode.PCONF_FILE,
                                      'runinterval',
                                       r'[0-9]+'))
        self.assertEqual(interval, expected)
        expected = _get_puppet_option(PuppetNode.PCONF_FILE,
                                      'server',
                                       r'[-A-Za-z0-9.]+$')
        self.assertEqual(fqdn, expected)

    def test_puppet_server_config(self):
        puppet = PuppetNode()
        puppet.load()
        dns_suffix = '*.%s.org' % _generate_word()
        options = {'server-auto-sign-policy': True,
                   'server-autosign-pattern': dns_suffix, }
        puppet.set_service_settings(options)
        logger.debug('Am I a master? %s' % puppet.is_master())
        with open(PuppetNode.ASIGN_FILE, 'r') as f:
                expected = f.read()
        self.assertEqual(dns_suffix, expected)


class TestValidateIP(unittest.TestCase):
    """Unit Tests for ValidateIP class """

    def test_valid_mask(self):
        """ Testing Validity of Net mask"""
        self.assertEqual(ValidateIP.ensure_valid_mask(
                '255.255.255.0'), '255.255.255.0')
        self.assertEqual(ValidateIP.ensure_valid_mask(
                '255.255.128.0'), '255.255.128.0')
        self.assertEqual(ValidateIP.ensure_valid_mask(
                '128.0.0.0'), '128.0.0.0')
        self.assertEqual(ValidateIP.ensure_valid_mask(
                '0.0.0.0'), '0.0.0.0')
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_mask, ('255.255.128.1'))

    def test_last_ip_less_than_first(self):
        """ test if last ip less than first """
        self.assertTrue(ValidateIP.is_last_ip_less_than_first(
                '192.168.1.10', '192.168.1.10'))
        self.assertTrue(ValidateIP.is_last_ip_less_than_first(
                '192.168.1.10', '192.168.1.100'))
        self.assertTrue(ValidateIP.is_last_ip_less_than_first(
                '192.168.1.10', '192.168.1.20'))
        self.assertRaises(Exception,
                ValidateIP.is_last_ip_less_than_first, (
                                            '192.168.1.100', '192.168.1.20'))

    def test_ensure_ip_in_network(self):
        """ ensure if ip is in network """
        self.assertEqual(ValidateIP.ensure_ip_in_network(
                '192.168.1.1', '255.255.255.0', '192.168.1.10', "first_ip"),
                '192.168.1.10')
        self.assertEqual(ValidateIP.ensure_ip_in_network(
                    '192.168.1.1', '255.255.255.0', '192.168.1.10', "last_ip"),
                '192.168.1.10')
        self.assertEqual(ValidateIP.ensure_ip_in_network(
                    '10.10.2.95', '255.255.128.0', '10.10.120.1', "first_ip"),
                '10.10.120.1')
        self.assertEqual(ValidateIP.ensure_ip_in_network(
                '10.5.5.10', '255.254.0.0', '10.4.0.8', "last_ip"), '10.4.0.8')
        self.assertEqual(ValidateIP.ensure_ip_in_network(
                 '192.168.7.80', '255.255.255.128', '192.168.7.2', "first_ip"),
                '192.168.7.2')
        self.assertEqual(ValidateIP.ensure_ip_in_network(
                '192.168.9.99', '255.255.255.192', '192.168.9.66', "last_ip"),
                '192.168.9.66')
        self.assertRaises(Exception, ValidateIP.ensure_ip_in_network, (
                '192.168.1.1', '255.255.255.0', '192.168.4.10', "first_ip"))
        self.assertRaises(Exception, ValidateIP.ensure_ip_in_network, (
                '10.10.2.95', '255.255.128.0', '10.9.9.90', "first_ip"))
        self.assertRaises(Exception, ValidateIP.ensure_ip_in_network, (
                '192.168.9.99', '255.255.255.192', '192.168.8.10', "first_ip"))
        self.assertRaises(Exception, ValidateIP.ensure_ip_in_network, (
                '192.168.7.80', '255.255.255.128', '192.168.8.50', "first_ip"))
        self.assertRaises(Exception, ValidateIP.ensure_ip_in_network, (
                '10.5.5.10', '255.254.0.0', '10.3.0.2', "last_ip"))

    def test_convert_mask_to_cidr(self):
        """ testing converstion of mask """
        self.assertEqual(ValidateIP.convert_mask_to_cidr(
                                                        '255.255.255.255'), 32)
        self.assertEqual(ValidateIP.convert_mask_to_cidr(
                                                        '255.255.255.0'), 24)
        self.assertEqual(ValidateIP.convert_mask_to_cidr(
                                                        '255.255.128.0'), 17)
        self.assertEqual(ValidateIP.convert_mask_to_cidr(
                                                        '128.0.0.0'), 1)
        self.assertEqual(ValidateIP.convert_mask_to_cidr(
                                                        '0.0.0.0'), 0)
        self.assertRaises(Exception,
                ValidateIP.convert_mask_to_cidr, (
                                                    '255.255.128.1'))
        self.assertRaises(Exception,
                ValidateIP.convert_mask_to_cidr, (
                                                    '255.73.128.1'))
        self.assertRaises(Exception,
                ValidateIP.convert_mask_to_cidr, (
                                                    '255.255.0.1'))
        self.assertRaises(Exception,
                ValidateIP.convert_mask_to_cidr, (
                                                    '255.0.128.1'))

    def test_ensure_valid_address(self):
        self.assertEqual(ValidateIP.ensure_valid_address('192.168.1.1', \
                                                'ip'), '192.168.1.1')
        self.assertEqual(ValidateIP.ensure_valid_address('10.10.10.1', \
                                                'ip'), '10.10.10.1')
        self.assertEqual(ValidateIP.ensure_valid_address('123.120.36.65', \
                                                'ip'), '123.120.36.65')
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_address, ('192.168.1', 'ip'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_address, ('.192.168.1.1', 'ip'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_address, ('192.256.1.1', 'ip'))

    def test_ensure_valid_hostname(self):
        """ tests for validating hostname """
        self.assertEqual(ValidateIP.ensure_valid_hostname('master', \
                                                'hostname'), 'master')
        self.assertEqual(ValidateIP.ensure_valid_hostname('my-master', \
                                                'hostname'), 'my-master')
        self.assertEqual(ValidateIP.ensure_valid_hostname('mast3r', \
                                                'hostname'), 'mast3r')
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_hostname, ('mast*r', \
                                                'hostname'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_hostname, ('mastr.', \
                                                'hostname'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_hostname, ('12master', \
                                                'hostname'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_hostname, ('master.client', \
                                                'hostname'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_hostname, ('.master', \
                                                'hostname'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_hostname, ('', 'hostname'))

    def test_ensure_valid_dns_suffix(self):
        self.assertEqual(ValidateIP.ensure_valid_dns_suffix(
                        'openstack.com', 'dns_suffix'), 'openstack.com')
        self.assertEqual(ValidateIP.ensure_valid_dns_suffix(
                        'openstack.co.in', 'dns_suffix'), 'openstack.co.in')
        self.assertEqual(ValidateIP.ensure_valid_dns_suffix(
                        'a.b.c.d', 'dns_suffix'), 'a.b.c.d')
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_dns_suffix, ('', \
                                                'dns_suffix'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_dns_suffix, ('.openstack.com', \
                                                'dns_suffix'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_dns_suffix, ('open stack.com', \
                                                'dns_suffix'))
        self.assertRaises(Exception,
                ValidateIP.ensure_valid_dns_suffix, ('123.com', \
                                                'dns_suffix'))


def _generate_word():
    char_array = 'abcdefghijklmnopqrstuvwxyz'
    word = ''
    for _ in range(0, 8):
        word += char_array[random.randint(0, 25)]
    return word


def _get_puppet_option(config_file, option_name, option_match_regex):
    retVal = None
    match_re = re.compile(r'\s*' + option_name + \
                          '\s* = (' + option_match_regex + ')\s*$',
                          re.IGNORECASE)
    puppet_opts = commands.getoutput('cat %s' % config_file).split("\n")
    for line in puppet_opts:
        match = match_re.match(line)
        if match:
            retVal = match.group(1)
            break
    return retVal
