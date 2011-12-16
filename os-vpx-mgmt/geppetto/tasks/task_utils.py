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

import collections
import datetime
import json
import random
import time

from functools import wraps

from djcelery.models import TaskState
from celery.result import AsyncResult

from geppetto.geppettolib import puppet
from geppetto.tasks import node_state

from geppetto.core import Failure
from geppetto.core.models import Node
from geppetto.core.models.infrastructure import ReportStatus


def puppet_kick(f):
    @wraps(f)
    def inner(*args, **kwargs):
        result = f(*args, **kwargs)
        for node_fqdn in result['node_fqdns']:
            try:
                node = Node.get_by_name(node_fqdn)
                node.set_report_status(ReportStatus.Pending)
            except Failure:
                # the node might have been removed, don't worry
                # but let's still kick a puppet run
                pass
            puppet.remote_puppet_run_async(node_fqdn)
        return result
    return inner


def puppet_check(f):
    @wraps(f)
    def inner(*args, **kwargs):
        config = f(*args, **kwargs)
        if 'dont_wait' in config and config['dont_wait']:
            return
        node_fqdns = config['node_fqdns']
        if len(node_fqdns) == 0:
            return

        tags = []
        for _, value in config.iteritems():
            if isinstance(value, collections.Iterable):
                tags.extend(value)
            else:
                continue

        random.seed()
        # Execute the task after a random number of seconds (base + delta)
        countdown = 60 + random.randint(1, 15)
        start = datetime.datetime.now() + datetime.timedelta(seconds=countdown)
        for i in xrange(1, 10):
            try:
                result = node_state.monitor.apply_async(args=[node_fqdns,
                                                              start,
                                                              tags],
                                                        countdown=countdown)
                return result.task_id
            except IOError, e:
                logger = node_state.monitor.get_logger()
                logger.warning('Waiting for new socket connection(%d).' % i)
                logger.exception(e)
                time.sleep(10)
        return 'N/A'
    return inner


def get_task_result(task_id):
    # TODO - wrap exceptions?
    return AsyncResult(task_id)


def get_task_ids_by_tags(tags):
    """return all task_ids for tasks whose tags include all the specified"""
    raw_tasks = TaskState.objects.filter(name=node_state.TASK_MONITOR_NAME)

    tasks = {}
    for raw_task in raw_tasks:
        id = raw_task.task_id
        if raw_task.kwargs != "{}":
            info = json.loads(raw_task.kwargs.replace("'", '"'))
            info['date'] = raw_task.tstamp
            tasks[id] = info

    matching_tasks = []
    for id, info in tasks.iteritems():
        current_tags = info["tags"]
        match = True
        for tag in tags:
            if not (tag in current_tags):
                match = False
        if match:
            matching_tasks.append(id)

    return matching_tasks
