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
import re
import urllib2
import yaml

from geppetto.geppettolib import network

logger = logging.getLogger("geppetto.core.views.yaml_utils")
STRIP_YAML = re.compile("!ruby/[a-zA-Z0-9:]* *")


def parse_string(yaml_string, regex_eval=True):
    if regex_eval:
        yaml_with_ruby_types_stripped = STRIP_YAML.sub("", yaml_string)
        return yaml.load(yaml_with_ruby_types_stripped)
    return yaml.load(yaml_string)


def get_node_facts(node_fqdn, facts_handler='REST'):
    """Reads the facts for the node, and returns them as a dictionary."""
    node_facts = facts_handlers[facts_handler](node_fqdn)
    facts_obj = parse_string(node_facts)
    #logger.debug("Got facts for node: %s" % node_fqdn)
    return {'facts_obj': facts_obj,
            'pickled_facts': pickle.dumps(facts_obj),
            'pretty_facts': pprint.pformat(facts_obj, 2), }


def _get_facts_file(node_fqdn):
    NODE_FACT_FILE = '/var/lib/puppet/puppet_facts/facts/%s.yaml'
    file_path = NODE_FACT_FILE % node_fqdn
    with open(file_path, 'r') as raw_yaml:
        return raw_yaml.read()


def _get_facts_rest(node_fqdn):

    def _make_request(request):
        # Let's try a few times if the remote agent is not ready
        for i in xrange(1, 10):
            try:
                return urllib2.urlopen(request)
            except urllib2.URLError:
                logger.warning('%s(%d): Unable to GET Facts URL'
                                                        % (node_fqdn, i))
        return None

    URL_PREFIX = 'https://%s:8140/production/facts/%s'
    master_fqdn = network.get_hostname()
    url = URL_PREFIX % (master_fqdn, node_fqdn)
    raw_yaml_request = urllib2.Request(url, headers={'Accept': 'yaml'})
    raw_yaml_fd = _make_request(raw_yaml_request)
    if raw_yaml_fd:
        return raw_yaml_fd.read()
        raw_yaml_fd.close()
    else:
        raise Exception('%s: Cannot GET facts' % url)


facts_handlers = {'FILE': _get_facts_file,
                  'REST': _get_facts_rest, }
