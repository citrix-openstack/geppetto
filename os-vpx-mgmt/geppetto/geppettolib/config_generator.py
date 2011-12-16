# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010 Citrix Systems, Inc.
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

# Generator of configuration files for network and core services

import logging

TEMPLATES_PATH = '/usr/share/geppetto'

IFCFG_TEMPLATE_FILE = 'interface.template'
IFCFG_DHCP_TEMPLATE_FILE = 'interface_dhcp.template'
NETWK_TEMPLATE_FILE = 'network.template'
RESLV_TEMPLATE_FILE = 'resolv_conf.template'
DNSMASQ_TEMPLATE_FILE = 'dnsmasq.d_os-vpx-mgmt.template'
NTPCF_TEMPLATE_FILE = 'ntp_conf.template'
HOSTS_TEMPLATE_FILE = 'hosts.template'

NAMED_CONF_TEMPLATE_FILE = 'named_conf.template'
NAMED_FORWARD_ZONE_TEMPLATE_FILE = 'forward_zone.template'
NAMED_REVERSE_ZONE_TEMPLATE_FILE = 'reverse_zone.template'

DHCPD_CONF_TEMPLATE_FILE = 'dhcpd_conf.template'
DHCPD_ARGS_TEMPLATE_FILE = 'dhcpd_args.template'


log = logging.getLogger('config_generator')


def fill_template(template_file, params_map):
    """Generate actual file from template"""
    path_to_template_file = '%s/%s' % (TEMPLATES_PATH, template_file)
    with open(path_to_template_file) as f:
        current_config = f.read() % params_map
    return current_config


def write_config(config, path_to_file):
    """Write content to file"""
    with open(path_to_file, 'w') as f:
        f.write(config)


def apply_config(template_file, config_file, **kwargs):
    """Write configuration to file"""
    try:
        write_config(fill_template(template_file,
                                   kwargs),
                                   config_file)
        return True
    except IOError, e:
        log.error(e)
        return False


if __name__ == "__main__":
    # If invoked directly generate sample configuration
    config_map = {'interface': '192.168.1.1',
                  'hostname': 'master',
                  'dhcp_server': '192.168.1.1',
                  'subnet': '192.168.1.0',
                  'subnet_mask': '255.255.255.0',
                  'broadcast_address': '192.168.1.255',
                  'routers': '192.168.1.254',
                  'dns_server': '192.168.1.1',
                  'dns_suffix': 'openstack.com',
                  'range_from': '192.168.1.10',
                  'range_to': '192.168.1.100',
                  'nic': 'eth1',
                  'reverse_zone_prefix': '1.168.192',
                  'puppet_master': 'fake', }

    config = {NAMED_CONF_TEMPLATE_FILE: '/etc/named.conf',
              NAMED_FORWARD_ZONE_TEMPLATE_FILE: '/var/named/zone.%s' %
                                                    config_map['dns_suffix'],
              NAMED_REVERSE_ZONE_TEMPLATE_FILE: '/var/named/%s.zone' %
                                            config_map['reverse_zone_prefix'],
              DHCPD_CONF_TEMPLATE_FILE: '/usr/share/geppetto/dhcpd.conf',
              DHCPD_ARGS_TEMPLATE_FILE: '/usr/share/geppetto/dhcpd',
              RESLV_TEMPLATE_FILE: '/usr/share/geppetto/resolv.conf',
              DNSMASQ_TEMPLATE_FILE: '/etc/dnsmasq.d/os-vpx-mgmt.conf',
              }

    for (template_file, config_file) in config.items():
        write_config(fill_template(template_file, config_map), config_file)
