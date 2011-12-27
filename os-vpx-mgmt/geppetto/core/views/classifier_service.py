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

from django.template import Context
from django.template import loader

from geppetto.core.models import utils
from geppetto.core.models import Role

from geppetto.core.models.configdefinition import get_default_settings
from geppetto.core.models.nodeconfiguration import override_defaults
from geppetto.core.models.roledependencies import get_config_classes
from geppetto.core.models.roledependencies import filter_enabled_services
from geppetto.core.views.xmlrpc import GenerateDjangoXMLRPCHandler

logger = logging.getLogger('geppetto.core.views.classifier_service')


class Service():
    """Service used by the Puppet External Node Classifier"""

    def get_configuration(self, node_fqdn):
        """Return the configuration of a VPX node.

        For testing, invoke the classifier directly:

        /usr/local/bin/puppet/classifier vpx_node_fqdn"""
        node = utils.get_or_create_node(node_fqdn)
        # Update configuration by:
        # 1) getting the list of roles applied to the node
        # 2) getting the list of configs that the roles depend on
        # 3) getting their current values (overrides and non)
        # 4) determining which roles are enabled services and which aren't
        all_role_assignments = node.get_role_assignments()
        config_classes = get_config_classes(all_role_assignments)
        settings = get_default_settings(config_classes)
        if node.get_group():
            override_defaults(settings, node.get_group_overrides())
        override_defaults(settings, node.get_overrides())
        running_services = filter_enabled_services(all_role_assignments)
        # add running_services as a list of tags as Puppet does not like
        # to convert arrays to strings
        settings['VPX_TAGS'] = str(running_services)[1:-1]
        stopped_services = managed_services - set(running_services)
        # Sort results, to make them deterministic, for unit testing.
        running_services.sort()
        stopped_services = list(stopped_services)
        stopped_services.sort()
        # Generate Configuration in YAML
        c = Context({'classes': frozenset(config_classes),
                     'running_services': running_services,
                     'stopped_services': stopped_services,
                     'settings': settings})
        return "%s" % loader.get_template("core/recipes.yaml").render(c)


managed_services = Role.get_service_roles()
svc = GenerateDjangoXMLRPCHandler(Service())
