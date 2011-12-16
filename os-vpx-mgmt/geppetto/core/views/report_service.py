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

import logging
import pickle
import string

from django.http import HttpResponse

from geppetto.core.models import Node
from geppetto.core.views import yaml_utils

from geppetto.core.models.infrastructure import ReportStatus

logger = logging.getLogger("geppetto.core.views.report_service")


def process_report(request):
    """This function is called by the puppetmaster's reporting system."""
    node = None
    try:
        report_details = parse_node_report(request.raw_post_data)
        node = Node.get_by_name(report_details['node_fqdn'])
        node.set_report(report_details)
        return HttpResponse(report_details['node_fqdn'], mimetype="text/plain")
    except Exception, e:
        logger.exception(e)
        return HttpResponse(str(e), status=500, mimetype="text/plain")
    finally:
        if node:
            node.save()


def parse_node_report(report_string):
    """This takes the puppet report format 2 (puppet 2.6.5 and higher)
    as a string, and saves the data into the django database.

    Returns the fqdn of the node the report came from"""
    report_obj = yaml_utils.parse_string(report_string)
    log = ''
    if report_obj["status"] != "unchanged":
        logs = []
        for log in report_obj["logs"]:
            logs.append("%s: %s" % (log["source"], log["message"]))
        log = string.join(logs, "\n")
    logger.debug("Got report for node: %s" % report_obj["host"])
    return {'node_fqdn': report_obj["host"],
            'report_time': report_obj["time"],
            'report_status': report_obj["status"],
            'status_code': ReportStatus.r_choices[report_obj["status"]],
            'report_obj': report_obj,
            'pickled_report': pickle.dumps(report_obj),
            'report_log': log, }
