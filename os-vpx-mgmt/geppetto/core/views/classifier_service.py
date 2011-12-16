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
from geppetto.core.models import Override
from geppetto.core.models import Role

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
        # 1) getting the list of the services running on the node
        # 2) getting the list of configs to be updated on the node
        # 3) getting the current values for the configs
        # 4) determining if there are overrides
        running_services = node.get_enabled_services()
        config_classes = _get_all_config_classes(node.get_roles())
        settings = _get_default_settings(config_classes)
        if node.get_group():
            _override_defaults(settings, node.get_group_overrides())
        _override_defaults(settings, node.get_overrides())
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


def _get_all_config_classes(roles):
    configs = []
    for role in roles:
        configs.extend(role.get_config_classes())
    return configs


def _get_default_settings(configs):
    settings = {}
    for config in configs:
        settings = dict(settings.items() + config.get_params_dict().items())
    return settings


def _override_defaults(settings, overrides):
    new_settings = settings
    for override in overrides:
        new_settings[override.config_class_parameter.name] = override.value
        if type(override) is Override:
            is_applied = override.node.report_date and \
                         override.node.report_last_changed_date and \
                override.node.report_date > override.timestamp and \
                override.node.report_status != 'f' and \
                override.node.report_last_changed_date > override.timestamp
            if override.one_time_only and is_applied:
                override.delete()


managed_services = Role.get_service_roles()
svc = GenerateDjangoXMLRPCHandler(Service())
