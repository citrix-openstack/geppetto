""" Tests for functions in XSConsoleData in the firstboot directory """

import re
import stubout

from django.test import TestCase
from geppetto.firstboot.XSConsoleData import DataUtils
from geppetto.firstboot.XSConsoleLayout import Layout
from geppetto.firstboot.XSConsoleDialogueBases import InfoDialogue


class TestXSConsoleData(TestCase):

    test_cmdlist = [ \
            'ro root=LABEL=vpxroot console=xvc0  geppetto_client=true',
            'ro root=LABEL=vpxroot console=xvc0  geppetto_master=true',
            'ro root=LABEL=vpxroot console=xvc0',
            'ro root=LABEL=vpxroot console=xvc0  geppetto_master=true' + \
               ' geeppetto_default_networking=true',
            'ro root=LABEL=vpxroot console=xvc0  geppetto_master=true' + \
               ' geppetto_ip=10.10.5.5 geppetto_mask=255.255.255.0' + \
               ' geppetto_gw=10.10.5.1 geppetto_first_ip=10.10.5.100' + \
               ' geppetto_last_ip=10.10.5.190 geppetto_hostname=themaster' + \
               ' geppetto_dns_suffix=openstack.com',
            'ro root=LABEL=vpxroot console=xvc0  geppetto_master=true' + \
               ' geppetto_ip=10.10.5.5 geppetto_mask=255.255.255.0' + \
               ' geppetto_first_ip=10.10.5.100' + \
               ' geppetto_last_ip=10.10.5.190 geppetto_hostname=themaster' + \
               ' geppetto_dns_suffix=openstack.com',
            'ro root=LABEL=vpxroot console=xvc0  geppetto_master=true' + \
               ' geppetto_first_ip=10.10.5.100 geppetto_mask=255.255.255.0' + \
               ' geppetto_last_ip=10.10.5.190 geppetto_hostname=themaster' + \
               ' geppetto_dns_suffix=openstack.com',
            'ro root=LABEL=vpxroot console=xvc0  geppetto_master=true' + \
               ' geppetto_ip=192.10.5.5 geppetto_default_networking=true' + \
               ' geppetto_first_ip=10.10.5.100 geppetto_mask=255.255.255.0' + \
               ' geppetto_last_ip=10.10.5.190 geppetto_hostname=themaster' + \
               ' geppetto_dns_suffix=openstack.com']

    no_arg_result = {'hostname': '', 'ip': '', 'netmask': '', \
                        'gateway': '', 'ntp_server': '', 'dns_suffix': '', \
                            'first_ip': '', 'last_ip': ''}
    result_with_args = {'hostname': 'themaster', 'ip': '10.10.5.5', \
                         'netmask': '255.255.255.0', 'gateway': '10.10.5.1', \
                         'ntp_server': '', 'dns_suffix': 'openstack.com', \
                        'first_ip': '10.10.5.100', 'last_ip': '10.10.5.190'}

    def setUp(self):
        super(TestXSConsoleData, self).setUp()
        self.obj = DataUtils.Inst()
        self.stubs = stubout.StubOutForTesting()
        self.stubs.Set(Layout.Inst(), 'PushDialogue', lambda x: True)
        self.stubs.Set(InfoDialogue, '__init__', lambda x, y: None)

    def tearDown(self):
        super(TestXSConsoleData, self).tearDown()
        self.stubs.UnsetAll()

    def test_get_ip_settings_from_kernel_args_for_no_network_args0(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[0]
        self.assertEqual(self.obj.get_ip_settings_from_kernel_args(), \
                            self.no_arg_result)

    def test_get_ip_settings_from_kernel_args_for_no_network_args1(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[1]
        self.assertEqual(self.obj.get_ip_settings_from_kernel_args(), \
                            self.no_arg_result)

    def test_get_ip_settings_from_kernel_args_for_no_network_args2(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[2]
        self.assertEqual(self.obj.get_ip_settings_from_kernel_args(), \
                            self.no_arg_result)

    def test_get_ip_settings_from_kernel_args_for_no_network_args3(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[3]
        self.assertEqual(self.obj.get_ip_settings_from_kernel_args(), \
                            self.no_arg_result)

    def test_get_ip_settings_from_kernel_args_with_network_args0(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[4]
        self.assertEqual(self.obj.get_ip_settings_from_kernel_args(), \
                            self.result_with_args)

    def test_get_ip_settings_from_kernel_args_with_network_args1(self):
        result_without_gw = self.result_with_args
        result_without_gw["gateway"] = ''
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[5]
        self.assertEqual(self.obj.get_ip_settings_from_kernel_args(), \
                            result_without_gw)

    def test_kernel_option_specify_network_settings_no_network_args0(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[0]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    None)

    def test_kernel_option_specify_network_settings_no_network_args1(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[1]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    None)

    def test_kernel_option_specify_network_settings_no_network_args2(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[2]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    None)

    def test_kernel_option_specify_network_settings_no_network_args3(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[3]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    None)

    def test_kernel_option_specify_network_settings_with_network_args0(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[4]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    True)

    def test_kernel_option_specify_network_settings_with_network_args1(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[5]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    True)

    def test_kernel_option_specify_network_settings_with_network_args2(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[6]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    None)

    def test_kernel_option_specify_network_settings_with_network_args3(self):
        self.obj.get_kernel_cmdline = lambda: self.test_cmdlist[7]
        self.assertEqual(self.obj._kernel_option_specify_network_settings(), \
                                    False)
