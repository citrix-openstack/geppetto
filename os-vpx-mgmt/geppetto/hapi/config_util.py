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

import os
import ConfigParser
import StringIO


class HYPERVISOR:
    # To add support to a new hypervisor, do the following:
    # - Add *_API, *_API_DRIVER_INFO, and *_API_DRIVER_INFO
    # - Add entry to DRIVERS
    # - Add entry to HOST_TYPES
    # - Add Python module
    XEN_API = 'xenapi'
    XEN_API_DRIVER_INFO = ['geppetto.hapi.xenapi.session_driver',
                           'XenAPISessionDriver']
    XEN_API_DESCRIPTION = 'XCP/Citrix XenServer'
    XEN_API_DEFAULT_PUBLIC_NETWORK = "xenbr1"
    XEN_API_DEFAULT_GUEST_NETWORK = "xenbr0"
    XEN_API_DEFAULT_VLAN_IF = "eth1"

    ESX_API = 'vmwareapi'
    ESX_API_DESCRIPTION = 'VMWare ESXi'
    ESX_API_DRIVER_INFO = ['geppetto.hapi.vsphereapi.session_driver',
                           'VSphereAPISessionDriver']
    ESX_API_DEFAULT_PUBLIC_NETWORK = "vSwitch1"
    ESX_API_DEFAULT_GUEST_NETWORK = "vSwitch0"
    ESX_API_DEFAULT_VLAN_IF = "vmnic1"

    DRIVERS = {
               XEN_API: {'description': XEN_API_DESCRIPTION,
                         'driver_info': XEN_API_DRIVER_INFO,
                         'public_net': XEN_API_DEFAULT_PUBLIC_NETWORK,
                         'guest_net': XEN_API_DEFAULT_GUEST_NETWORK,
                         'default_vlan_if': XEN_API_DEFAULT_VLAN_IF, },

               ESX_API: {'description': ESX_API_DESCRIPTION,
                         'driver_info': ESX_API_DRIVER_INFO,
                         'public_net': ESX_API_DEFAULT_PUBLIC_NETWORK,
                         'guest_net': ESX_API_DEFAULT_GUEST_NETWORK,
                         'default_vlan_if': ESX_API_DEFAULT_VLAN_IF, },
               }

HOST_TYPES = (
    (HYPERVISOR.XEN_API, HYPERVISOR.XEN_API_DESCRIPTION),
    (HYPERVISOR.ESX_API, HYPERVISOR.ESX_API_DESCRIPTION),
)

TIME_BETWEEN_API_CALL_RETRIES = 2


def _detect_hypervisor():
    """This detection mechanism is only for XENAPI vs VMWARE."""
    return os.path.exists("/sys/hypervisor/uuid") and \
                HYPERVISOR.XEN_API or \
                HYPERVISOR.ESX_API


def get_running_hypervisor_description():
    return HYPERVISOR.DRIVERS[_detect_hypervisor()]['description']


def get_running_hypervisor_type():
    """Get type of underlying hypervisor."""
    return _detect_hypervisor()


def get_hypervisor_info():
    """Get driver information of the underlying hypervisor."""
    return HYPERVISOR.DRIVERS[_detect_hypervisor()]['driver_info']


def get_hypervisor_default_vlan_interface():
    return HYPERVISOR.DRIVERS[_detect_hypervisor()]['default_vlan_if']


def load_session(session_type=None):
    if session_type is None:
        hv_mod, hv_driver = get_hypervisor_info()
    else:
        hv_mod, hv_driver = HYPERVISOR.DRIVERS[session_type]['driver_info']
    runtime = __import__(hv_mod, globals(), locals(), [hv_driver], -1)
    return getattr(runtime, hv_driver)()


def parse_config(filename):
    with file(filename) as f:
        lines = f.readlines()
    if not lines or not lines[0]:
        raise Exception('Empty config file %s' % filename)
    if lines[0][0] != '[':
        lines.insert(0, '[DEFAULT]\n')
    config = ConfigParser.SafeConfigParser()
    config.readfp(StringIO.StringIO(''.join(lines)))
    config.filename = filename
    return config


def config_get(config, key, default=None, section='DEFAULT'):
    result = config.has_option(section, key) and \
             config.get(section, key) or \
             default
    if result is None:
        raise Exception('Missing config option %s %s.' % (section, key))
    if result and (result[0] == "'" or result[0] == '"'):
        result = eval(result)
    return result


def config_set(config, key, value, section='DEFAULT'):
    config.set(section, key, value)
    with open(config.filename, 'wb') as configfile:
        config.write(configfile)


def get_config_param(config_file, key, default_value):
    if os.access(config_file, os.F_OK):
        parse_result = parse_config(config_file)
        return config_get(parse_result, key)
    else:
        return default_value


def get_vpx_version():
    _version_config = parse_config('/etc/openstack/vpx-version')
    return config_get(_version_config, 'VPX_VERSION', 'unknown')
