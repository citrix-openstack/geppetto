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

from geppetto.geppettolib import setup
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

    def start_service(self, pre_script='', post_script=''):
        """Start service"""
        try:
            if pre_script != '':
                utils.execute(pre_script)
        except Exception, e:
            log.exception(e)
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
        try:
            if post_script != '':
                utils.execute(post_script)
        except Exception, e:
            log.exception(e)

    def stop_service(self):
        """Stop service"""
        try:
            utils.execute('service %s stop' % self.name)
        except Exception, e:
            log.error(e)
            raise Exception('Unable to execute command')


class GeppettoService():
    """This class is for managing Geppetto and related services"""
    GEPPETTO_BACKEND_FILE = '/etc/openstack/geppetto-backend'
    GEPPETTO_SETUP_SCRIPT = '/usr/local/bin/geppetto/init/geppetto-init'

    def __init__(self,
                 db_args={'svc_on': False, },
                 queue_args={'svc_on': True, },
                 geppetto_args={}):
        # first element: starting order
        # Second element: service name
        # Third element: pre-initialization script
        self.services = [(2, Service("citrix-geppetto")),
                         (2, Service("citrix-geppetto-celeryd")),
                         (2, Service("citrix-geppetto-celerycam")), ]
        self._db_init(db_args)
        self._queue_init(queue_args)
        self.apply_config(geppetto_args, db_args, queue_args)
        self.services.sort()

    def install_service(self):
        for svc in self.services:
            svc[1].install_service()

    def uninstall_service(self):
        for svc in self.services:
            svc[1].uninstall_service()

    def start_service(self):
        for svc_entry in self.services:
            if len(svc_entry) == 3:
                svc_entry[1].start_service(pre_script=svc_entry[2])
            else:
                svc_entry[1].start_service()

    def stop_service(self):
        for svc_entry in self.services:
                svc_entry[1].stop_service()

    def _db_init(self, db_args):
        if db_args['svc_on']:
            pre_script = ''
            if 'config' in db_args:
                pre_script = \
                         ('/usr/local/bin/geppetto/init/database-init '
                          '"%s" "%s" "%s"' % (db_args['config'][setup.DBNAME],
                                              db_args['config'][setup.DBUSER],
                                              db_args['config'][setup.DBPASS]))
            self.services.append((0, Service("mysqld"), pre_script))

    def _queue_init(self, queue_args):
        if queue_args['svc_on']:
            self.services.append((1, Service("rabbitmq-server")))

    @classmethod
    def apply_config(cls, geppetto_args={}, db_args={}, queue_args={}):
        args_list = []
        if 'config' in db_args:
            args_list.append(db_args['config'])
        if 'config' in queue_args:
            args_list.append(queue_args['config'])
        for args in args_list:
            for arg_label, arg_value in args.iteritems():
                utils.\
                update_config_option_strip_spaces(cls.GEPPETTO_BACKEND_FILE,
                        setup.MasterBootOptions[arg_label]['config_param'],
                        "'" + arg_value + "'")
        utils.execute(cls.GEPPETTO_SETUP_SCRIPT)
        # TODO update settings.py with things like DEBUG='value', etc.
