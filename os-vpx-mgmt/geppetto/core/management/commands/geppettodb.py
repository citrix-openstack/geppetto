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

from geppetto.core.models import utils

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    args = '[init | reset | password <password> | ...]'
    help = """Utility command for operations on the geppetto database:\n
           init              Set the DB to contain entries for the master.
           reset             Set the DB to a pristine state.
           root_password     Set root password to <password>."""

    def handle(self, *args, **options):
        try:
            if len(args) > 0:
                if args[0] == 'init':
                    utils.model_init()
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
