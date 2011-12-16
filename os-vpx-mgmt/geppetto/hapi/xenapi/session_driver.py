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

import atexit
import os
import XenAPI

from geppetto.hapi import config_util
from geppetto.hapi import interface
from geppetto.hapi import exception
from geppetto.hapi.xenapi import host_driver
from geppetto.hapi.xenapi import network_driver
from geppetto.hapi.xenapi import storage_driver
from geppetto.hapi.xenapi import vm_driver


class XenAPISessionDriver(interface.Session):
    """Abstraction layer for Host operations."""

    def __init__(self):
        """Initializer."""
        super(interface.Session, self).__init__()
        self._xapi = None
        self._vm_driver = None
        self._host_driver = None
        self._storage_driver = None
        self._network_driver = None
        atexit.register(lambda: self.logout())

    def login(self, username='root', password=None):
        url = _get_connection_url()
        config = config_util.parse_config('/etc/openstack/hapi')
        username = config_util.config_get(config, 'HAPI_USER', 'root')
        pwd = password != None and password or \
                            config_util.config_get(config, 'HAPI_PASS')
        if not pwd:
            raise exception.HAPIFailure(
                        exception.exc_codes.UNCLASSIFIED_PASSWORD_UNCONFIGURED,
                        exception.exc_strs.UNCLASSIFIED_PASSWORD_UNCONFIGURED)
        self._login(url, username, pwd, config_util.get_vpx_version())

    @property
    def Host(self):
        if self._host_driver is None:
            self._host_driver = host_driver.XenAPIHostDriver(self._xapi)
        return self._host_driver

    @property
    def Network(self):
        if self._network_driver is None:
            self._network_driver = \
                network_driver.XenAPINetworkDriver(self._xapi)
        return self._network_driver

    @property
    def Storage(self):
        if self._storage_driver is None:
            self._storage_driver = \
                storage_driver.XenAPIStorageDriver(self._xapi)
        return self._storage_driver

    @property
    def VM(self):
        if self._vm_driver is None:
            self._vm_driver = vm_driver.XenAPIVMDriver(self._xapi)
        return self._vm_driver

    def logout(self):
        try:
            if self._xapi is not None:
                self._xapi.xenapi.session.logout()
        except:
            pass

    def _login(self, url, username, password, version):
        try:
            self._xapi = XenAPI.Session(url)
            self._xapi._ServerProxy__transport.user_agent = \
                                                'os-vpx/%s' % version
            self._xapi.xenapi.login_with_password(username, password)
        except XenAPI.Failure, inner_exc:
            raise exception.HAPIFailure(
                    exception.exc_codes.UNCLASSIFIED_AUTHENTICATION_FAILURE,
                    exception.exc_strs.UNCLASSIFIED_AUTHENTICATION_FAILURE,
                    inner_exc)


def _get_connection_url():
    if os.access('/etc/openstack/xapi-url', os.F_OK):
        hapi_url_config = config_util.parse_config('/etc/openstack/xapi-url')
        return config_util.config_get(hapi_url_config, 'XAPI_URL',
                          'http://XAPI_URL_MISSING')
    else:
        return 'https://192.168.128.1'
