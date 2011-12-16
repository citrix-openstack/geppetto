""" Network related libraries for geppetto """
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


import ConfigParser
import commands
import logging
import re
import socket
import netaddr

from geppetto.geppettolib import config_generator
from geppetto.geppettolib import utils
from geppetto.geppettolib.utils import GeppettoConfigParser


log = logging.getLogger('network')

REGEX_DNS_VALIDATION = re.compile(r'^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*' +\
        '[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$')
REGEX_HOSTNAME_VALIDATION = re.compile(r'^(([a-zA-Z]|[a-zA-Z]' +\
        '[a-zA-Z0-9\-]*[a-zA-Z0-9])+)$')


def get_hostname():
    return socket.getfqdn()


class NetworkConfiguration():
    """This class is for network configuration"""

    IFCFG_FILE = '/etc/sysconfig/network-scripts/ifcfg-%s'
    NETWK_FILE = '/etc/sysconfig/network'
    RESLV_FILE = '/etc/resolv.conf'
    RESLV_IFACE_FILE = '/etc/resolv.conf.%s'
    DNSMASQ_FILE = "/etc/dnsmasq.d/os-vpx-mgmt.conf"
    NTPCF_FILE = '/etc/ntp.conf'
    HOSTS_FILE = '/etc/hosts'
    DHCLIENT_FILE = "/etc/dhclient-eth1.conf"

    INTERFACE = 0
    NETWORK = 1
    DNS = 2
    NTP = 3

    def __init__(self):
        self.activated = False

        self.device = ''
        self.bootproto = ''
        self.netmask = ''
        self.address = ''
        self.gateway = ''
        self.hostname = ''
        self.dns_server = ''        # TODO: handle multiple DNS/NTP entries?
        self.dns_suffix = ''
        self.dns_prefix = ''
        self.ntp_server = ''

        self._ifcfg_setup = False    # True if files have been set already
        self._netwk_setup = False
        self._reslv_setup = False
        self._ntpcf_setup = False

    def load_interface(self, device):
        """Load content of NetworkConfiguration.IFCFG_FILE
        in device, bootproto, netmask, address"""
        try:
            cfg = GeppettoConfigParser()
            cfg.read(NetworkConfiguration.IFCFG_FILE % device)
            self.device = cfg.get('main', 'DEVICE')
            self.bootproto = cfg.get('main', 'BOOTPROTO')
            self.address = cfg.get('main', 'IPADDR')
            self.netmask = cfg.get('main', 'NETMASK')
            self._ifcfg_setup = True
        except (ConfigParser.InterpolationDepthError, IOError), e:
            self._ifcfg_setup = False
            log.error(e)
        except (ConfigParser.NoOptionError), e:
            log.error(e)
            if self.bootproto == 'dhcp':
                # venture to take an educated guess on address and netmask
                [self.address, self.netmask] = \
                                    _get_address_netmask_tuple(device)
                self._ifcfg_setup = True

    def load_network(self):
        """Load content of NetworkConfiguration.NETWK_FILE
        in gateway and hostname"""
        try:
            cfg = GeppettoConfigParser()
            cfg.read(NetworkConfiguration.NETWK_FILE)
            self.hostname = cfg.get('main', 'HOSTNAME')[1:-1]
            self.gateway = cfg.get('main', 'GATEWAY')
            self._netwk_setup = True
        except (ConfigParser.InterpolationDepthError, IOError), e:
            log.error(e)
            self._netwk_setup = False
        except (ConfigParser.NoOptionError), e:
            # venture to take an educated guess on the gateway
            log.error(e)
            if self.device:
                self.gateway = _get_gateway(self.device)
                self._netwk_setup = True
            else:
                self._netwk_setup = False
                raise Exception('Unable to get gateway; load interface again')

    def load_dns(self):
        """Load content of NetworkConfiguration.RESLV_FILE
        in comma-separated format in dns_server and dns_suffix"""
        self.dns_server = ""
        self.dns_suffix = ""

        with open(NetworkConfiguration.RESLV_FILE) as f:
            for line in f.readlines():
                match = re.match(r'nameserver\s+(\S+)', line)
                if match:
                    self.dns_server = '%s, %s' % (match.group(1),
                                                  self.dns_server)
                else:
                    match = re.match(r'search\s+(\S+)', line)
                    if match:
                        if self.dns_suffix != '':
                            break
                        # FIXME - hack - only pick the first one
                        # (from eth1 not eth2) for now, need to
                        # deal with multiple properly
                        self.dns_suffix = '%s, %s' % (match.group(1),
                                                      self.dns_suffix)

        self.dns_server = self.dns_server[:-2]
        self.dns_suffix = self.dns_suffix[:-2]
        self._reslv_setup = self.dns_server != '' and self.dns_suffix != ''

    def load_ntp(self):
        """Load content of NetworkConfiguration.NTPCF_FILE
        in comma-separated format in ntp_server"""
        with open(NetworkConfiguration.NTPCF_FILE) as f:
            for line in f.readlines():
                match = re.match(r'server\s+(\S+)', line)
                if match and not match.group(1).startswith('127.127.'):
                    self.ntp_server = '%s, %s' % (match.group(1),
                                                  self.ntp_server)
        self.ntp_server = self.ntp_server[:-2]
        self._ntpcf_setup = self.ntp_server != ''

    def is_setup(self, config):
        """
        Return True if file related to config param given in input is set.

        config can be:      INTERFACE = 0
                            NETWORK =   1
                            DNS =       2
                            NTP =       3
        """
        if config == NetworkConfiguration.INTERFACE:
            return self._ifcfg_setup
        elif config == NetworkConfiguration.NETWORK:
            return self._netwk_setup
        elif config == NetworkConfiguration.DNS:
            return self._reslv_setup
        elif config == NetworkConfiguration.NTP:
            return self._ntpcf_setup

    def set_interface(self, dev, protocol, netm=None, addr=None):
        """Write info to NetworkConfiguration.IFCFG_FILE"""
        if protocol not in ['static', 'none', 'dhcp']:
            raise Exception('Invalid BOOTPROTO')
        if protocol == 'dhcp':
            self._ifcfg_setup = \
                config_generator.apply_config(
                                    config_generator.IFCFG_DHCP_TEMPLATE_FILE,
                                    NetworkConfiguration.IFCFG_FILE % dev,
                                    device=dev)
        elif protocol == 'static' or protocol == 'none':
            if netm is None or addr is None:
                raise \
        Exception('Missing netmask or address with BOOTPROTO=%s' % protocol)
            if not re.match(r'[0-9][-0-9.]*$', addr):
                raise Exception('Invalid address %s' % addr)
            self._ifcfg_setup = \
                config_generator.apply_config(
                                    config_generator.IFCFG_TEMPLATE_FILE,
                                    NetworkConfiguration.IFCFG_FILE % dev,
                                    device=dev,
                                    bootproto=protocol,
                                    netmask=netm,
                                    address=addr)
        if self._ifcfg_setup:
            self.device = dev
            self.netmask = netm
            self.address = addr

    def set_hostname_and_gateway(self, hn, gw='0.0.0.0'):
        """Write info to NetworkConfiguration.NETWK_FILE
        and update DHCLIENT_FILE"""
        if not re.match(r'[-A-Za-z0-9.]+$', hn):
            raise Exception('Invalid hostname %s' % hn)
        if not re.match(r'[0-9][-0-9.]*$', gw):
            raise Exception('Invalid gateway %s' % gw)

        gw_line = gw != '0.0.0.0' and 'GATEWAY=%s' % gw or ''

        self._netwk_setup = \
            config_generator.apply_config(
                                    config_generator.NETWK_TEMPLATE_FILE,
                                    NetworkConfiguration.NETWK_FILE,
                                    gateway=gw_line, hostname=hn)
        if self._netwk_setup:
            self.gateway = gw
            self.hostname = hn
            self._update_dhclient(hn)

    def _update_dhclient(self, hostname):
        """Updates the DHClient config to send the correct hostname"""
        config = """option puppet-master-name code 194 = text;
option os-vpx-reverse-dns-prefix code 195 = text;
send host-name "%s";
request;""" % hostname
        config_generator.write_config(config, self.DHCLIENT_FILE)

    def set_network(self, hn, dns_suff, gw='0.0.0.0'):
        """Write info to NetworkConfiguration.NETWK_FILE\
        and HOSTS_TEMPLATE_FILE"""
        self.set_hostname_and_gateway(hn, gw)

        self._netwk_setup = self._netwk_setup and \
            config_generator.apply_config(config_generator.HOSTS_TEMPLATE_FILE,
                                          NetworkConfiguration.HOSTS_FILE,
                                          hostname=hn, dns_suffix=dns_suff)

    def set_dns_server(self, server, suffix, prefix):
        """Write info to NetworkConfiguration.RESLV_FILE,
        NetworkConfiguration.RESLV_IFACE_FILE, and
        NetworkConfiguration.DNSMASQ_FILE."""
        def apply_cfg(f):
            return config_generator.apply_config(
                config_generator.RESLV_TEMPLATE_FILE, f,
                dns_server=server,
                dns_suffix=suffix,
                reverse_zone_prefix=prefix)
        apply_cfg(NetworkConfiguration.RESLV_IFACE_FILE % self.device)
        self._reslv_setup = apply_cfg(NetworkConfiguration.RESLV_FILE)
        if self._reslv_setup:
            self.dns_server = server
            self.dns_suffix = suffix
            self.dns_prefix = prefix
        config_generator.apply_config(
            config_generator.DNSMASQ_TEMPLATE_FILE,
            NetworkConfiguration.DNSMASQ_FILE,
            dns_server=server,
            dns_suffix=suffix,
            reverse_zone_prefix=prefix)

    def set_ntp_server(self, server):
        """Write info to NetworkConfiguration.NTPCF_FILE"""
        self._ntpcf_setup = \
            config_generator.apply_config(config_generator.NTPCF_TEMPLATE_FILE,
                                          NetworkConfiguration.NTPCF_FILE,
                                          ntp_server=server)
        if self._ntpcf_setup:
            self.ntp_server = server

    def enforce_configuration(self):
        """Try to restart the network service: only root can succeed"""
        try:
            utils.execute('hostname %s' % self.hostname)
            utils.execute('service network restart')     # only RHEL-based
            self.activated = True
        except Exception, e:
            log.error(e)
            self.activated = False

MASK_MAP = {'0': 0,
            '128': 1,
            '192': 2,
            '224': 3,
            '240': 4,
            '248': 5,
            '252': 6,
            '254': 7,
            '255': 8}


class ValidateIP:
    """ Methods to validate network settings """

    @classmethod
    def ensure_valid_address(cls, address, setting):
        """
        This function checks if the ip address given is valid
        """
        if setting in ['gateway', 'dns_server', 'ntp_server'] and\
            address == '':
            return '0.0.0.0'
        try:
            socket.inet_aton(address)
        except socket.error:
            raise Exception("Invalid %s." % setting)
        split_ip = address.split('.')
        if not (len(split_ip) == 4):
            raise Exception("Invalid %s." % setting)
        return address

    @classmethod
    def convert_mask_to_cidr(cls, mask):
        """
        This function converts mask into cidr e.g '255.255.128.0' -> 17.
        It raises an exception if the mask entered is invalid or returns
        the cidr as an integer if the mask is valid
        """
        split_mask = mask.split('.')
        if len(split_mask) != 4:
            raise Exception("Invalid Network Mask")
        mask_sum = 0
        for i in split_mask:
            if i in MASK_MAP:
                mask_sum += MASK_MAP[i]
            else:
                raise Exception("Invalid Network Mask")
        return mask_sum

    @classmethod
    def ensure_ip_in_network(cls, address, mask, check_address, setting):
        """
        This function checks if check_address lies in the network formed
        using address and mask. It doesn't check if the address or mask is
        valid in itself which can be done using _ensure_valid_address()
        and ensure_valid_mask()
        """
        cidr = cls.convert_mask_to_cidr(mask)
        network_address = address + '/' + str(cidr)
        given_network = netaddr.IPNetwork(network_address)
        check_ip = netaddr.IPAddress(check_address)
        if check_ip in given_network:
            return check_address
        else:
            raise Exception(
                    "%s doesn't fall in the specified network" % setting)

    @classmethod
    def ensure_valid_mask(cls, mask):
        """
        This function checks if the netmask entered (e.g '255.255.128.0') is a
        valid mask. It will raise an exception if the mask is invalid or return
        the mask if its valid.
        """
        cls.convert_mask_to_cidr(mask)
            #it will raise exception if the mask is invalid
        return mask

    @classmethod
    def is_last_ip_less_than_first(cls, first_ip, last_ip):
        """
        This function simply compares if last_ip is less than first_ip
        It doesn't check if the given ips are valid for which
        ensure_valid_address() should be used
        """
        first_split = first_ip.split('.')
        last_split = last_ip.split('.')
        for i in range(4):
            if int(last_split[i]) < int(first_split[i]):
                raise Exception("Last IP is less than first IP")
        return True

    @classmethod
    def ensure_valid_hostname(cls, name, setting):
        """ Validating the hostname """
        match = REGEX_HOSTNAME_VALIDATION.match(name)
        if not match:
            raise Exception('Invalid ' + setting)
        return name

    @classmethod
    def ensure_valid_dns_suffix(cls, name, setting):
        """ Validating the dns suffix """
        match = REGEX_DNS_VALIDATION.match(name)
        if not match:
            raise Exception('Invalid ' + setting)
        return name


def _get_address_netmask_tuple(device):
    address = ''
    netmask = ''
    ipre = r'[0-9a-f.:]+'
    ifRE = re.compile(r'\s*inet\s+addr\s*:(' + ipre + \
                      ')\s+bcast\s*:\s*' + ipre + \
                      r'\s+mask\s*:\s*(' + ipre + r')\s*$',
                      re.IGNORECASE)
    ifconfig = commands.getoutput('/sbin/ifconfig %s' % device).split("\n")
    for line in ifconfig:
        match = ifRE.match(line)
        if match:
            address = match.group(1)
            netmask = match.group(2)
            break
    return [address, netmask]


def _get_gateway(device):
    retVal = ''
    routeRE = re.compile(
        r'([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+UG\s+\d+\s+\d+\s+\d+\s+' + \
        device, re.IGNORECASE)
    routes = commands.getoutput("/sbin/route -n").split("\n")
    for line in routes:
        match = routeRE.match(line)
        if match:
            retVal = match.group(2)
            break
    return retVal
