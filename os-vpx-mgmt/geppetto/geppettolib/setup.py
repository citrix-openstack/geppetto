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

import re

DBENGINE = 'dbengine'
DBNAME = 'dbname'
DBHOST = 'dbhost'
DBUSER = 'dbuser'
DBPASS = 'dbpass'
QUEUEHOST = 'queuehost'
QUEUEUSER = 'queueuser'
QUEUEPASS = 'queuepass'

MasterBootOptions = {DBENGINE: {'default': 'sqlite3',
                                'options': ['sqlite3', 'mysql'],
                                'config_param': 'VPX_MASTER_DB_BACKEND', },
                     DBNAME: {'options': ['/var/lib/geppetto/sqlite3.db~',
                                          'geppetto'],
                              'config_param': 'VPX_MASTER_DB_NAME', },
                     DBHOST: {'options': ['', 'localhost'],
                              'config_param': 'VPX_MASTER_DB_HOST', },
                     DBUSER: {'options': ['', 'root'],
                              'config_param': 'VPX_MASTER_DB_USER', },
                     DBPASS: {'options': ['', 'citrix'],
                              'config_param': 'VPX_MASTER_DB_PASS', },

                     QUEUEHOST: {'options': ['localhost'],
                                 'config_param': 'VPX_MASTER_QUEUE_HOST', },
                     QUEUEUSER: {'options': ['guest'],
                                 'config_param': 'VPX_MASTER_QUEUE_USER', },
                     QUEUEPASS: {'options': ['guest'],
                                 'config_param': 'VPX_MASTER_QUEUE_PASS', }, }


def database_setup(cmdline):
    dbconf = parse_boot_options(cmdline,
                                DBENGINE, [DBHOST, DBNAME, DBUSER, DBPASS])
    db_run = dbconf[DBHOST] == 'localhost' and dbconf[DBENGINE] == 'mysql'
    return {'svc_on': db_run,
            'config': dbconf}


def queue_setup(cmdline):
    queueconf = parse_boot_options(cmdline,
                                   None, [QUEUEHOST, QUEUEUSER, QUEUEPASS])
    queue_run = queueconf[QUEUEHOST] == 'localhost'
    return {'svc_on': queue_run,
            'config': queueconf, }


def parse_boot_options(cmdline, key, options):
    settings = {}
    if key:
        settings[key] = \
                _get_option_value(cmdline, key,
                                  MasterBootOptions[key]['default'])
        idx = MasterBootOptions[key]['options'].index(settings[key])
    else:
        idx = 0

    for opt in options:
        settings[opt] = _get_option_value(cmdline, opt,
                                  MasterBootOptions[opt]['options'][idx])
    return settings


def _get_option_value(kwargs, option, default=None):
    match = re.compile(r'.* ' + option + '=([^ ]+).*').match(kwargs)
    if match:
        return match.groups()[0]
    else:
        return default
