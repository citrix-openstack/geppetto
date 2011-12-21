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

import ConfigParser
import logging
import ipcalc
import os
import subprocess
import string
import StringIO

from functools import wraps

logger = logging.getLogger('utils')
_safechars = frozenset(string.ascii_letters + string.digits + '@%_-+=:,./')


def quote(file):
    """Return a shell-escaped version of the file string."""
    for c in file:
        if c not in _safechars:
            break
    else:
        if not file:
            return "''"
        return file
    # use single quotes, and put single quotes into double quotes
    # the string $'b is then quoted as '$'"'"'b'
    return "'" + file.replace("'", "'\"'\"'") + "'"


def execute(command, ignore_codes=[]):
    logger.debug('Executing: %s' % command)

    env = os.environ.copy()
    process = subprocess.Popen(command,
                               shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env=env)
    (out, err) = process.communicate()
    logger.debug('Got: stdout(%(out)s) stderr(%(err)s)' % locals())
    if process.returncode != 0 and process.returncode not in ignore_codes:
        logger.error('Error code: %s' % process.returncode)
        raise Exception('Command output: %(out)s %(err)s' % locals())
    elif process.returncode > 0:
        logger.warning('Error code: %s is ignored.' % process.returncode)
    return (out, err)


def ipinfo(address, netmask):
    """Return information about the ip address and netmask given in in"""
    binary_representation = ipcalc.IP(netmask).bin()
    mask = binary_representation.count('1', 0, len(binary_representation))
    calc = ipcalc.Network(address, mask)
    subnet = str(calc.network())
    broadcast = str(calc.broadcast())
    netclass = ipcalc.IP(address).info()
    if netclass == 'CLASS B':
        octects = subnet.split('.')
        reverse_zone = '%s.%s' % (octects[1], octects[0])
    else:
        octects = subnet.split('.')
        reverse_zone = '%s.%s.%s' % (octects[2], octects[1], octects[0])
    return [subnet, broadcast, reverse_zone]


def trace(newlogger):
    """Trace entry, exit and exceptions."""
    def deco_trace(f):
        def f_trace(*args, **kwargs):
            newlogger.debug('ENTER: %s' % f.__name__)
            try:
                result = f(*args, **kwargs)
            except Exception, e:
                newlogger.exception('EXCEPTION %s %s' % (f.__name__, e))
                raise
            newlogger.debug('EXIT: %s' % f.__name__)
            return result
        return f_trace
    return deco_trace


def get_trace_decorator(newlogger):
    def trace2(f):
        @wraps(f)
        def f_trace(*args, **kwargs):
            newlogger.debug('ENTER: %s' % f.__name__)
            try:
                result = f(*args, **kwargs)
            except Exception, e:
                newlogger.exception('EXCEPTION %s %s' % (f.__name__, e))
                raise
            newlogger.debug('EXIT: %s' % f.__name__)
            return result
        return f_trace
    return trace2


def update_config_option(file_path, option_name, option_value):
    base_cmd = ('sed -e "s,%(option_name)s = .*,%(option_name)s = '
                '%(option_value)s," -i %(file_path)s')
    execute(base_cmd % locals())


def update_config_option_strip_spaces(file_path, option_name, option_value):
    base_cmd = ('sed -e "s,%(option_name)s=.*,%(option_name)s='
               '%(option_value)s," -i %(file_path)s')
    execute(base_cmd % locals())


class GeppettoConfigParser(ConfigParser.ConfigParser):
    """To read config files without section headers"""
    def read(self, filename):
        try:
            text = open(filename).read()
        except IOError, e:
            logger.error(e)
            raise e
        else:
            file = StringIO.StringIO("[main]\n" + text)
            self.readfp(file, filename)
