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

from django.core import validators
from djcelery.models import TaskState
from celery.result import AsyncResult

from geppetto.tasks import node_state
from geppetto.core import exception_handler
from geppetto.core import exception_messages

from geppetto.core.models.infrastructure import ReportStatus


def puppet_kick(f):
    @wraps(f)
    def inner(*args, **kwargs):
        config = f(*args, **kwargs)

        dont_wait = config.get('dont_wait', False)
        node_fqdns = config.get('node_fqdns', [])
        if dont_wait or len(node_fqdns) == 0:
            return

        # set Node status to Pending
        node_state.set_report_status(node_fqdns,
                                     ReportStatus.Pending)

        tags = []
        for _, value in config.iteritems():
            if isinstance(value, collections.Iterable):
                tags.extend(value)
            else:
                continue

        random.seed()
        # Execute the task after a random number of seconds
        countdown = random.randint(1, 15)
        start = datetime.datetime.now() + datetime.timedelta(seconds=countdown)
        sender = [f.__name__, str(args), str(kwargs)]
        for i in xrange(1, 10):
            try:
                t = node_state.\
                  monitor.apply_async(args=[node_fqdns, start],
                                      kwargs={'tags': tags,
                                              'sender': sender,
                                              'retries': 0, },
                                      countdown=countdown)
                return t.task_id
            except IOError, e:
                logger = node_state.monitor.get_logger()
                logger.warning('Waiting for new socket connection(%d).' % i)
                logger.exception(e)
                time.sleep(10)
        return 'N/A'
    return inner


@exception_handler(exception_messages.not_found)
def get_task(task_id):
    try:
        return AsyncResult(task_id)
    except:
        raise validators.ValidationError('Unable to retrieve task')


def get_task_details(task_uuid):
        task_result = get_task(task_uuid)
        details = {'status': task_result.state,
                   'result': task_result.result}
        if task_result.failed():
            details['traceback'] = task_result.traceback
        return details


def get_uuids():
    return [t.task_id for t in TaskState.objects.all()]


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


def chunks(l, chunk_size=3):
    for i in xrange(0, len(l), chunk_size):
        yield l[i:i + chunk_size]
