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


"""
:mod:`tasks` -- Tasks to deploy and configure an OpenStack cloud
================================================================
"""


import logging

from geppetto.tasks import node_state

from celery.signals import after_setup_logger
from celery.signals import after_setup_task_logger


def after_setup_logger_handler(sender=None, logger=None, loglevel=None,
                               logfile=None, format=None,
                               colorize=None, **kwds):
    while len(logger.handlers) > 0:
        hldr = logger.handlers[0]
        logger.removeHandler(hldr)
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    handler.setFormatter(logging.Formatter('geppetto-celery ' + format))
    handler.setLevel(loglevel)
    logger.addHandler(handler)

after_setup_logger.connect(after_setup_logger_handler)
after_setup_task_logger.connect(after_setup_logger_handler)
