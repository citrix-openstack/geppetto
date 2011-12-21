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

import random
import xmlrpclib

from celery import task as celery_task
from celery import exceptions as celery_exceptions

from django.conf import settings
from geppetto.geppettolib import puppet
from geppetto.core.views import service_proxy
from geppetto.core.models.infrastructure import Node
from geppetto.core.models.infrastructure import ReportStatus

TASK_MONITOR_NAME = 'tasks.node_state.monitor'


@celery_task.task(name=TASK_MONITOR_NAME,
                  max_retries=settings.GEPPETTO_TASK_MAX_RETRIES)
def monitor(node_fqdns, start_time, tags=None, sender=None, retries=0):
    """Controls that configuration changes are applied to the nodes."""
    logger = monitor.get_logger()
    details_dict = {}
    try:
        logger.debug("%s: retrieving details." % node_fqdns)
        master_fqdn = puppet.PuppetNode.get_puppet_option('server')
        svc = service_proxy.create_proxy(master_fqdn, 8080,
                                         service_proxy.Proxy.Geppetto, 'v1')
        details_dict = svc.Node.get_details(node_fqdns)
    except xmlrpclib.Fault:
        logger.exception("%s: Unable to retrieve details" % node_fqdns)

    try:
        affected_nodes = node_fqdns
        for node_fqdn, details in details_dict.iteritems():
            logger.debug("%s: configuration changed. "
                         "Checking status." % node_fqdn)
            date = details['report_date'] and \
                   details['report_date'] or start_time
            status = details['report_status'] and \
                     details['report_status'] or ReportStatus.Pending
            logger.debug("%s[%s]: configuration "
                         "status(%s)" % (node_fqdn, date, status))
            if (status == ReportStatus.Disabled) or \
               (status == ReportStatus.Stable and date > start_time):
                affected_nodes.remove(node_fqdn)
    except Exception, e:
        logger.exception(e)

    if len(affected_nodes) > 0:
        logger.debug("%s: configuration not applied yet." % affected_nodes)
        try:
            for node_fqdn in affected_nodes:
                puppet.remote_puppet_run_async(node_fqdn)

            random.seed()
            countdown = settings.GEPPETTO_TASK_RETRY_DELAY + \
                                                    random.randint(1, 15)
            return monitor.retry(args=[affected_nodes, start_time],
                                 kwargs={'tags': tags,
                                         'sender': sender,
                                         'retries': retries + 1},
                                 countdown=countdown)
        except celery_exceptions.MaxRetriesExceededError:
            logger.exception("%s: configuration failed "
                             "to apply." % affected_nodes)
            set_report_status(affected_nodes, ReportStatus.Failed)
            raise Exception("Following nodes are "
                            "not stable: %s" % affected_nodes)

    logger.debug("%s: configuration applied" % tags)
    return tags


def set_report_status(node_fqdns, status):
    for node_fqdn in node_fqdns:
        node = Node.safe_get_by_name(str(node_fqdn))
        if node:
            node.set_report_status(status)
