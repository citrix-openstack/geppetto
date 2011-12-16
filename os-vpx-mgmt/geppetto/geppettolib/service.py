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

import commands
import logging

from geppetto.geppettolib import utils


log = logging.getLogger('geppetto')


class Service():
    """This class is for managing Geppetto"""
    def __init__(self, name):
        self.name = name

    def service_status(self):
        """Return the status of the service"""
        cmd = 'service %s status | awk \'{print $3}\''
        status = commands.getoutput(cmd % self.name)
        if status in ['started', 'stopped']:
            return status
        else:
            return 'unknown'

    def install_service(self):
        """Add service to bootstrap list"""
        try:
            utils.execute('chkconfig --level 2345 %s on' % self.name)
        except Exception, e:
            log.error(e)
            raise Exception('Unable to execute command')

    def uninstall_service(self):
        """Remove service from bootstrap list"""
        try:
            utils.execute('chkconfig %s off' % self.name)
        except Exception, e:
            log.error(e)
            raise Exception('Unable to execute command')

    def start_service(self):
        """Start service"""
        try:
            utils.execute('service %s start' % self.name)
        except Exception, e:
            # If we fail, try restart
            log.exception(e)
            try:
                utils.execute('service %s restart' % self.name)
            except Exception, e:
                # if restart fails too, raise exc
                log.exception(e)
                raise Exception('Unable to execute command')

    def stop_service(self):
        """Stop service"""
        try:
            utils.execute('service %s stop' % self.name)
        except Exception, e:
            log.error(e)
            raise Exception('Unable to execute command')


class GeppettoService():
    """This class is for managing Geppetto and related services"""
    def __init__(self):
        self.services = [Service("citrix-geppetto"),
                         Service("citrix-geppetto-celeryd"),
                         Service("citrix-geppetto-celerycam"),
                         Service("rabbitmq-server"), ]

    def install_service(self):
        for svc in self.services:
            svc.install_service()

    def uninstall_service(self):
        for svc in self.services:
            svc.uninstall_service()

    def start_service(self):
        for svc in self.services:
            svc.start_service()

    def stop_service(self):
        for svc in self.services:
            svc.stop_service()
