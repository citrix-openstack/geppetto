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

from geppetto.wsgi import run_eventlet_server

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    args = '[optional port number, or ipaddr:port]'
    help = 'Starts an eventlet wsgi server.'

    def handle(self, *args, **options):
        try:
            port = 8080
            host = '0.0.0.0'
            if len(args) == 1 and args[0].find(':') == -1:
                port = int(args[0])
            elif len(args) == 1 and args[0].find(':') != -1:
                endpoint = args[0].split(':')
                host = endpoint[0]
                port = endpoint[1]
            run_eventlet_server(int(port), host)
        except Exception, e:
            raise CommandError(e)
