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

from optparse import make_option

from geppetto.core.models import utils

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    args = '[init | reset | password <password> | ...]'
    help = """Utility command for operations on the geppetto database:\n
           init [options]    Set the DB to contain entries for the master.
           reset             Set the DB to a pristine state.
           root_password     Set root password to <password>."""

    option_list = BaseCommand.option_list + (
        make_option('--db_backend', help='The DB driver'),
        make_option('--db_name', help='The DB name'),
        make_option('--db_host', help='The DB host fqdn'),
        make_option('--db_user', help='The DB user'),
        make_option('--db_pass', help='The user password'),
        make_option('--queue_host', help='The Message Queue fqdn'),
        make_option('--queue_user', help='The Queue user'),
        make_option('--queue_pass', help='The user password'),
        )

    def handle(self, *args, **options):
        try:
            if len(args) > 0:
                if args[0] == 'init':
                    configs = options
                    del configs['verbosity']
                    del configs['settings']
                    del configs['pythonpath']
                    del configs['traceback']
                    utils.model_init(**configs)
                elif args[0] == 'reset':
                    utils.model_reset()
                elif args[0] == 'root_password':
                    try:
                        utils.set_root_password(args[1])
                    except:
                        raise CommandError('Invalid password.')
                else:
                    raise CommandError('Option not supported.')
            else:
                raise CommandError('Missing or invalid arguments.')
        except Exception, e:
            raise CommandError(e)
