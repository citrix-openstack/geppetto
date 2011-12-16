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
import re

from threading import Timer
from geppetto.geppettolib import utils

log = logging.getLogger('geppettolib.puppet')


class PuppetNode():
    """This class is for puppet configuration"""

    STATE_FILE = '/var/lib/geppetto/vpx_role'
    PCONF_FILE = '/etc/puppet/puppet.conf'
    ASIGN_FILE = '/etc/puppet/autosign.conf'

    UNKNOWN = -1
    MASTER = 0
    PUPPET = 1

    def __init__(self):
        self._master_flag = PuppetNode.UNKNOWN

    def load(self):
        """Load Status information about this node"""
        try:
            with open(PuppetNode.STATE_FILE, 'r') as f:
                self._master_flag = int(f.read())
        except (IOError, ValueError), e:
            log.error(e)
            self._master_flag = PuppetNode.UNKNOWN
        else:
            if self._master_flag not in [PuppetNode.UNKNOWN,
                                         PuppetNode.MASTER,
                                         PuppetNode.PUPPET]:
                raise Exception('Corrupted VPX State, please reset!')

    def get_puppet_option(self, opt):
        """Read configuration 'opt' from PuppetNode.PCONF_FILE"""
        regex = {'runinterval': r'[0-9]+',
                 'server': r'[-A-Za-z0-9.]+$',
                 'autosign': r'(.+?)(\.[^.]*$|$)', }
        if opt in ['runinterval', 'server', 'autosign']:
            return _get_puppet_option(PuppetNode.PCONF_FILE,
                                      opt,
                                      regex[opt])
        else:
            raise Exception('Puppet option not supported: %s' % opt)

    def is_master(self):
        """Returns None if unknown or True if master, False if node"""
        if self._master_flag == PuppetNode.UNKNOWN:
            return None
        elif self._master_flag == PuppetNode.MASTER:
            return True
        elif self._master_flag == PuppetNode.PUPPET:
            return False

    def set_node_flag(self, flag):
        if flag not in [PuppetNode.MASTER, PuppetNode.PUPPET]:
            raise Exception('Invalid node flag')
        with open(PuppetNode.STATE_FILE, 'w') as f:
            f.write(str(flag))
        self._master_flag = flag

    def install_service(self):
        """Add service to bootstrap list"""
        self._do_action_on_service('chkconfig --level 2345', 'on')
        #TODO(armandomi): that's dodgy and must go. It is related to
        # bug report:
        # http://projects.puppetlabs.com/issues/6297
        if self._master_flag == PuppetNode.MASTER:
            try:
                self._do_action_on_service('service', 'start')
            except Exception, e:
                log.error(e)

    def uninstall_service(self):
        """Remove service from bootstrap list"""
        self._do_action_on_service('chkconfig', 'off')

    def start_service(self):
        """Start service"""
        self._do_action_on_service('service', 'start')

    def stop_service(self):
        """Stop service"""
        self._do_action_on_service('service', 'stop')

    def set_service_settings(self, configuration):
        """
        Setup the service on host with the given configuration kwargs
        kwargs currently supported are:

        client-* options are supported on the Node
        server-* options are supported on the Master

        client-poll-interval     - The period between configurations
                                   in seconds. Default 60 seconds
        client-master-reference  - The name of the master for this
                                   Puppet node. Default master
        server-auto-sign-policy  - True if puppet client can sign with
                                   master automatically. Default False.
        server-autosign-pattern  - The pattern which the hostname should
                                   match against. Default * (very insecure)
        """
        def _set_client(settings):
            if 'client-poll-interval' in settings:
                new_value = int(settings['client-poll-interval'])
                utils.update_config_option(PuppetNode.PCONF_FILE,
                                           'runinterval',
                                           new_value)
            if 'client-master-reference' in settings:
                hostname = r'[-A-Za-z0-9.]+$'
                if not re.match(hostname, settings['client-master-reference']):
                    raise Exception('Invalid hostname %s' % \
                                    settings['client-master-reference'])
                utils.update_config_option(PuppetNode.PCONF_FILE,
                                           'server',
                                           settings['client-master-reference'])

        def _set_server(settings):
            if 'server-auto-sign-policy' not in settings:
                return
            if settings['server-auto-sign-policy'] is True and \
               'server-autosign-pattern' in settings:
                new_value = PuppetNode.ASIGN_FILE
                # update autosignfile.conf
                try:
                    with open(new_value, 'w') as f:
                        f.write(settings['server-autosign-pattern'])
                except IOError, e:
                    log.error(e)
            elif settings['server-auto-sign-policy'] is False:
                new_value = 'false'
            # update PCONF_FILE
            utils.update_config_option(PuppetNode.PCONF_FILE,
                                       'autosign',
                                       new_value)

        options = ['client-poll-interval',
                   'client-master-reference',
                   'server-auto-sign-policy',
                   'server-autosign-pattern', ]
        c_sets = {}
        s_sets = {}
        for opt, val in configuration.items():
            if opt.startswith('client') and opt in options:
                c_sets[opt] = val
            elif opt.startswith('server') and opt in options:
                s_sets[opt] = val
            else:
                raise Exception('Unsupported Setting')
        c_num = len(c_sets)
        s_num = len(s_sets)
        if c_num != 0 and s_num != 0:
            raise Exception('Ambiguous setting')
        if c_num > 0:
            _set_client(c_sets)
        else:
            _set_server(s_sets)

    def _do_action_on_service(self, command, action):
        """Execute action on the service"""
        if self._master_flag is None:
            raise Exception('Master flag is None: invalid action')

        service = 'puppet'
        if self._master_flag == PuppetNode.MASTER:
            service += 'master'
        try:
            utils.execute('%s %s %s' % (command, service, action))
        except Exception, e:
            log.error(e)
            raise Exception('Unable to execute command')


def _get_puppet_option(config_file, option_name, option_match_regex):
    match_re = re.compile(r'\s*' + \
                          option_name + \
                          '\s* = (' + \
                          option_match_regex + \
                          ')\s*$',
                          re.IGNORECASE)
    puppet_opts = commands.getoutput('cat %s' % config_file).split("\n")
    for line in puppet_opts:
        match = match_re.match(line)
        if match:
            retVal = match.group(1)
            break
    return retVal


def remote_puppet_run(node_fqdn, foreground=True):
    try:
        # ignores exit code 3: this means that a puppet run is already
        # in execution.
        flag = ' -f' if foreground else ''
        utils.execute('sudo puppetrun --host %s%s' % (node_fqdn,
                                                       flag), [3])
    except Exception, e:
        log.exception(e)


def remote_puppet_run_async(node_fqdn):
    def _run_async():
        remote_puppet_run(node_fqdn, False)
    t = Timer(0.1, lambda: _run_async())
    t.start()
