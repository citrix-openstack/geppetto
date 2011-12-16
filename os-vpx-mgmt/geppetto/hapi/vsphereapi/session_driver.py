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
import time

from geppetto.hapi import config_util
from geppetto.hapi import exception
from geppetto.hapi import interface
from geppetto.hapi.vsphereapi import error_util
from geppetto.hapi.vsphereapi import host_driver
from geppetto.hapi.vsphereapi import network_driver
from geppetto.hapi.vsphereapi import storage_driver
from geppetto.hapi.vsphereapi import vm_driver
from geppetto.hapi.vsphereapi import vim


class VSphereAPISessionDriver(interface.Session):
    """Session driver for vSphere API session."""

    def __init__(self):
        """Initializer."""
        super(interface.Session, self).__init__()
        self._vsphereapi = None
        self._vm_driver = None
        self._host_driver = None
        self._storage_driver = None
        self._network_driver = None
        atexit.register(lambda: self.logout())

    def login(self, username='root', password=None):
        host = _get_connection_url()
        config = config_util.parse_config('/etc/openstack/hapi')
        username = config_util.config_get(config, 'HAPI_USER', 'root')
        pwd = password != None and password or \
                            config_util.config_get(config, 'HAPI_PASS')
        if not pwd:
            raise exception.HAPIFailure(
                        exception.exc_codes.UNCLASSIFIED_PASSWORD_UNCONFIGURED,
                        exception.exc_strs.UNCLASSIFIED_PASSWORD_UNCONFIGURED)

        wsdl_directory = config_util.config_get(config, 'WSDL_LOC',
                                               '/etc/openstack/visdk')
        if not wsdl_directory:
            raise exception.HAPIFailure(
                    exception.exc_codes.UNCLASSIFIED_MISSING_VMWAREWSDL_FILES,
                    exception.exc_strs.UNCLASSIFIED_MISSING_VMWAREWSDL_FILES)
        wsdl_file = "file://" + wsdl_directory + "/vimService.wsdl"
        self._login(host, username, pwd, wsdl_file,
                    config_util.get_vpx_version())

    @property
    def Host(self):
        if self._host_driver is None:
            self._host_driver = \
                host_driver.VSphereAPIHostDriver(self._vsphereapi)
        return self._host_driver

    @property
    def Network(self):
        if self._network_driver is None:
            self._network_driver = \
                network_driver.VSphereAPINetworkDriver(self._vsphereapi)
        return self._network_driver

    @property
    def Storage(self):
        if self._storage_driver is None:
            self._storage_driver = \
                storage_driver.VSphereAPIStorageDriver(self._vsphereapi)
        return self._storage_driver

    @property
    def VM(self):
        if self._vm_driver is None:
            self._vm_driver = vm_driver.VSphereAPIVMDriver(self._vsphereapi)
        return self._vm_driver

    def _login(self, host, username, password, wsdl_file, version):
        """Creates a session with the ESX host."""
        try:
            self._vsphereapi = VSphereAPISession(host,
                                                 username,
                                                 password,
                                                 wsdl_file)
        except Exception, inner_exc:
            raise exception.HAPIFailure(
                    exception.exc_codes.UNCLASSIFIED_AUTHENTICATION_FAILURE,
                    exception.exc_strs.UNCLASSIFIED_AUTHENTICATION_FAILURE,
                    inner_exc)

    def logout(self):
        try:
            if self._vsphereapi is not None:
                self._vsphereapi._logout()
        except:
            pass


class VSphereAPISession(object):
    """Manages a session with the ESX host and handles
    vSphere API calls made to the host.
    """

    def __init__(self, host=None, user="root", password=None,
                 wsdl_file=None, api_retry_count=10, scheme="https"):
        self.api_retry_count = api_retry_count
        self.host = host
        self.user = user
        self.password = password
        self.scheme = scheme
        self.wsdl_file = wsdl_file
        self._session_id = None
        self.vim = None
        self._create_session()
        self.service_content = self.vim.get_service_content()
        self.client_factory = self.vim.client.factory

    def _create_session(self):
        """Creates a session with the ESX host."""
        while True:
            try:
                # Login and setup the session with the ESX host for making
                # API calls
                self.vim = self._get_vim_object()
                session = self.vim.Login(
                               self.vim.get_service_content().sessionManager,
                               userName=self.user,
                               password=self.password)
                # Terminate the earlier session, since there is a limit
                # to the number of sessions a client can own
                if self._session_id:
                    try:
                        self.vim.TerminateSession(
                                self.vim.get_service_content().sessionManager,
                                sessionId=[self._session_id])
                    except Exception, excep:
                        print(excep)
                self._session_id = session.key
                return
            except Exception, excep:
                excep.message = "In vsphereapi _create_session, " \
                                "exception while creating session. " + excep
                raise excep

            except Exception, inner_exc:
                raise exception.HAPIFailure(
                      exception.exc_codes.UNCLASSIFIED_AUTHENTICATION_FAILURE,
                      exception.exc_strs.UNCLASSIFIED_AUTHENTICATION_FAILURE,
                      inner_exc)

    def _logout(self):
        """Logs-out the session."""
        try:
            self.vim.Logout(self.vim.get_service_content().sessionManager)
        except:
            pass

    def _get_vim_object(self):
        """Create the VIM Object instance."""
        return vim.Vim(protocol=self.scheme,
                       host=self.host,
                       wsdl_file=self.wsdl_file)

    def _get_vim(self):
        """Gets the VIM object reference."""
        if self.vim is None:
            self._create_session()
        return self.vim

    def _is_vim_object(self, module):
        """Check if the module is a VIM Object instance."""
        return isinstance(module, vim.Vim)

    def _call_method(self, module, method, *args, **kwargs):
        """
        Calls a method within the module specified with
        args provided.
        """
        args = list(args)
        retry_count = 0
        exc = None
        last_fault_list = []
        while True:
            try:
                if not self._is_vim_object(module):
                    # If it is not the first try, then get the latest
                    # vim object
                    if retry_count > 0:
                        args = args[1:]
                    args = [self.vim] + args
                else:
                    module = self.vim

                retry_count += 1
                temp_module = module

                for method_elem in method.split("."):
                    temp_module = getattr(temp_module, method_elem)

                return temp_module(*args, **kwargs)
            except error_util.VimFaultException, excep:
                # If it is a Session Fault Exception, it may point
                # to a session gone bad. So we try re-creating a session
                # and then proceeding ahead with the call.
                exc = excep
                if error_util.FAULT_NOT_AUTHENTICATED in excep.fault_list:
                    if error_util.FAULT_NOT_AUTHENTICATED in last_fault_list:
                        return []
                    last_fault_list = excep.fault_list
                    self._create_session()
                else:
                    # No re-trying for errors for API call has gone through
                    # and is the caller's fault. Caller should handle these
                    # errors. e.g, InvalidArgument fault.
                    break
            except error_util.SessionOverLoadException, excep:
                # For exceptions which may come because of session overload,
                # we retry
                exc = excep
            except Exception, excep:
                # If it is a proper exception, say not having furnished
                # proper data in the SOAP call or the retry limit having
                # exceeded, we raise the exception
                exc = excep
                break
            # If retry count has been reached then break and
            # raise the exception
            if retry_count > self.api_retry_count:
                break
            time.sleep(config_util.TIME_BETWEEN_API_CALL_RETRIES)

        print("In vsphereapi:_call_method, "
                     "got this exception: %s") % exc
        raise


def _get_connection_url():
    if os.access('/etc/openstack/vmware-url', os.F_OK):
        hapi_url_config = config_util.parse_config('/etc/openstack/vmware-url')
        return config_util.config_get(hapi_url_config, 'VMWARE_HOST',
                          'VMWARE_HOST_MISSING')
    else:
        return None
