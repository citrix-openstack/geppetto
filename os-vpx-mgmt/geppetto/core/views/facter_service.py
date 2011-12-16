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
import pprint

from geppetto.core import Failure
from geppetto.core.models import Node
from geppetto.core.views import yaml_utils
from geppetto.core.views.xmlrpc import GenerateDjangoXMLRPCHandler

logger = logging.getLogger('geppetto.core.views.facter_service')


class Service():
    """Service used by Facter to send facts about a node"""

    def process_facts(self, node_fqdn, facts):
        """This function is called by the puppetmaster's reporting system."""
        node = None
        try:
            node = Node.get_by_name(node_fqdn)
            node.set_facts(parse_node_facts(facts))
            auth_status = node.is_authenticated()
            if auth_status is None:
                logger.warning("(%s): Unable to get facts: not "
                               "authenticated." % node_fqdn)
            elif auth_status is False:
                logger.warning("(%s): Unable to get facts: bad "
                               "credentials." % node_fqdn)
        except Failure, e:
            # get_by_name must have raised a not_found exception.
            logger.warning('%s: waiting for the node to register.' % node_fqdn)
        except Exception, e:
            logger.exception(e)
        finally:
            if node:
                node.save()


def parse_node_facts(yaml_blob):
    """Reads the facts for the node, and returns them as a dictionary."""
    facts_obj = yaml_utils.parse_string(yaml_blob, False)
    return {'facts_obj': facts_obj,
            'pickled_facts': pickle.dumps(facts_obj),
            'pretty_facts': pprint.pformat(facts_obj, 2), }


svc = GenerateDjangoXMLRPCHandler(Service())
