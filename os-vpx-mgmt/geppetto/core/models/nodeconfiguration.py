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

import datetime
import logging

import configdefinition
import infrastructure
import roledependencies

from django.db import models

from geppetto.core import exception_handler
from geppetto.core import exception_messages

logger = logging.getLogger('geppetto.core.models')


class NodeRoleAssignment(models.Model):
    node = models.ForeignKey(infrastructure.Node)
    role = models.ForeignKey(roledependencies.Role)
    enabled = models.BooleanField()
    last_updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("role", "node")
        ordering = ["node"]
        app_label = "core"
        db_table = 'core_noderoleassignment'

    def __unicode__(self):
        return "Node:" + self.node.fqdn + " Role:" + self.role.name

    @classmethod
    @exception_handler(exception_messages.non_unique)
    def copy_role_assignments_to_node(cls, role_assignments, node):
        roles = []
        for ra in role_assignments:
            try:
                roles.append(ra.role)
                existing_ra = cls.objects.get(node=node, role=ra.role)
                existing_ra.enabled = ra.enabled
                existing_ra.last_updated = datetime.datetime.now()
                existing_ra.save()
            except NodeRoleAssignment.DoesNotExist:
                cls.objects.create(node=node,
                                   role=ra.role,
                                   enabled=ra.enabled)
        return roles

    @classmethod
    @exception_handler(exception_messages.non_unique)
    def add_roles_to_node(cls, node, roles, enable=False):
        for role in roles:
            cls.objects.create(node=node, role=role, enabled=enable)

    @classmethod
    def exists(cls, node, role):
        try:
            cls.objects.get(node=node, role=role)
            return True
        except NodeRoleAssignment.DoesNotExist:
            return False


class Override(models.Model):
    node = models.ForeignKey(infrastructure.Node)
    config_class_parameter = models.\
                            ForeignKey(configdefinition.ConfigClassParameter)
    value = models.CharField(max_length=200)
    one_time_only = models.BooleanField()
    timestamp = models.DateTimeField('Applied at', null=True,
                                     blank=True, auto_now_add=True)

    class Meta:
        unique_together = ("node", "config_class_parameter")
        ordering = ["node"]
        app_label = "core"
        db_table = 'core_override'

    def __unicode__(self):
        return "Node: %s, ConfigParam: %s" % (self.node.fqdn,
                                              self.config_class_parameter.name)

    @classmethod
    def update_or_create_override(cls, node, param, value, one_time=False):
        try:
            param.validate(value)
            override = cls.objects.get(node=node, config_class_parameter=param)
            override.value = value
            override.one_time_only = one_time
            override.save()
        except Override.DoesNotExist:
            cls.objects.create(node=node,
                               config_class_parameter=param,
                               value=value,
                               one_time_only=one_time)

    @classmethod
    def copy_node_overrides(cls, node, overrides):
        for override in overrides:
            cls.update_or_create_override(node,
                                          override.config_class_parameter,
                                          override.value,
                                          override.one_time_only)

    @classmethod
    def get_by_node_and_param(cls, node, param):
        try:
            return cls.objects.get(node=node,
                                   config_class_parameter=param)
        except Override.DoesNotExist:
            return None

    @classmethod
    def update_overrides(cls, param):
        for override in cls.objects.filter(config_class_parameter=param):
            override.value = param.default_value
            override.save()

    @classmethod
    @exception_handler(exception_messages.not_found)
    def remove_override(cls, param, node):
        override = cls.objects.get(node=node, config_class_parameter=param)
        override.delete()


class GroupOverride(models.Model):

    NETWORK_WORKERS = "NETWORK_WORKERS"

    group = models.ForeignKey(infrastructure.Group)
    config_class_parameter = models.\
                            ForeignKey(configdefinition.ConfigClassParameter)
    value = models.CharField(max_length=200)

    class Meta:
        unique_together = ("group", "config_class_parameter")
        ordering = ["group"]
        app_label = "core"
        db_table = 'core_groupoverride'

    def __unicode__(self):
        return "Group: %s, ConfigParam: %s" % (self.group.name,
                                              self.config_class_parameter.name)

    @classmethod
    @exception_handler(exception_messages.non_unique)
    def create(cls, group, param_label, param_value):
        try:
            param = \
               configdefinition.ConfigClassParameter.get_by_name(param_label)
            param.validate(param_value)
            cls.objects.get(group=group, config_class_parameter=param)
        except GroupOverride.DoesNotExist:
            cls.objects.create(group=group,
                               config_class_parameter=param,
                               value=param_value)

    @classmethod
    @exception_handler(exception_messages.not_found)
    def remove_override(cls, group, param):
        override = cls.objects.get(group=group,
                                   config_class_parameter=param)
        override.delete()

    @classmethod
    def update_overrides(cls, param):
        for override in cls.objects.filter(config_class_parameter=param):
            override.value = param.default_value
            override.save()


def override_defaults(settings, overrides):
    new_settings = settings
    for override in overrides:
        new_settings[override.config_class_parameter.name] = override.value
        if type(override) is Override:
            is_applied = override.node.report_date and \
            override.node.report_last_changed_date and \
            override.node.report_date > override.timestamp and \
            override.node.report_status != infrastructure.ReportStatus.Failed \
            and override.node.report_last_changed_date > override.timestamp
            if override.one_time_only and is_applied:
                override.delete()
