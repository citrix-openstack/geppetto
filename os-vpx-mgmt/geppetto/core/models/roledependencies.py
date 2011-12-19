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
import configdefinition

from django.db import models

from geppetto.core import exception_handler
from geppetto.core import exception_messages
from geppetto.core.models.configdefinition import ConfigClassParameter


logger = logging.getLogger('geppetto.core.models')


DEFAULT_ROLES = ['os-vpx-set-geppetto-properties',
                 'os-vpx-cli-nova',
                 'os-vpx-cli-glance',
                 'os-vpx-cli-swift',
                 'os-vpx-logging', ]


class RoleDescription(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]
        app_label = "core"
        db_table = 'core_roledescription'

    def __unicode__(self):
        return self.name

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_by_name(cls, description_name):
        return cls.objects.get(name=description_name)

    @classmethod
    def get_compositions(cls):
        return dict((d.name, [r.name for r in d.role_set.all()]) \
                                          for d in cls.objects.all())

    def get_composition(self):
        return [r.name for r in self.role_set.all()]


class Role(models.Model):
    # Nova Core roles
    MYSQL = "mysqld"
    RABBITMQ = "rabbitmq-server"
    # Dashboard
    OPENSTACK_DASHBOARD = "openstack-dashboard"
    # Nova services
    NOVA_AJAX_CONSOLE_PROXY = "openstack-nova-ajax-console-proxy"
    NOVA_API = "openstack-nova-api"
    NOVA_COMPUTE = "openstack-nova-compute"
    NOVA_NETWORK = "openstack-nova-network"
    NOVA_SCHEDULER = "openstack-nova-scheduler"
    NOVA_VNCPROXY = "openstack-nova-vncproxy"
    NOVA_VOLUME = "openstack-nova-volume"
    # Glance roles
    GLANCE_API = "openstack-glance-api"
    GLANCE_REGISTRY = "openstack-glance-registry"
    # Swift roles
    SWIFT_ACCOUNT = "openstack-swift-account"
    SWIFT_CONTAINER = "openstack-swift-container"
    SWIFT_MEMCACHE = "memcached"
    SWIFT_PROXY = "openstack-swift-proxy"
    SWIFT_OBJECT = "openstack-swift-object"
    SWIFT_RSYNC = "openstack-swift-rsync"
    # Geppetto utility roles
    IMG_CONTAINER = "os-vpx-image-container"
    RING_BUILDER = "os-vpx-ring-builder"
    CELERY_WORKER = "citrix-geppetto-celeryd"
    CELERY_CAMERA = "citrix-geppetto-celerycam"
    # Experimental
    LBSERVICE = "openstack-lb-service"
    # Keystone services
    KEYSTONE_AUTH = "openstack-keystone-auth"
    KEYSTONE_ADMIN = "openstack-keystone-admin"

    name = models.CharField(max_length=200, unique=True, db_index=True)
    service = models.BooleanField(default=True)
    internal = models.BooleanField(default=False)
    config_classes = models.ManyToManyField(configdefinition.ConfigClass,
                                           through='RoleConfigClassAssignment')
    description = models.ForeignKey(RoleDescription, null=True, blank=True,
                                    on_delete=models.SET_NULL)

    class Meta:
        ordering = ["name"]
        app_label = "core"
        db_table = 'core_role'

    def __unicode__(self):
        return self.name

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_by_name(cls, role_name):
        return cls.objects.get(name=role_name)

    @classmethod
    def get_service_roles(cls):
        """The list of service roles that are available in OpenStack"""
        return set([role.name for role in \
                        cls.objects.filter(service=True, internal=False)])

    @classmethod
    def get_roles_dict(cls, is_service=True, is_internal=False):
        return dict((role.name, role.description \
                                     and role.description.name or '')
                    for role in \
                        cls.objects.filter(service=is_service,
                                           internal=is_internal))

    @classmethod
    def get_default_roles(cls):
        return cls.objects.filter(name__in=DEFAULT_ROLES)

    def get_config_classes(self):
        return [rel.config_class \
                for rel in self.roleconfigclassassignment_set.all()]

    def get_config_labels(self):
        classes = [rel.config_class \
                   for rel in self.roleconfigclassassignment_set.all()]
        return [param.name for param in \
                ConfigClassParameter.objects.filter(config_class__in=classes)]


class RoleConfigClassAssignment(models.Model):
    role = models.ForeignKey(Role)
    config_class = models.ForeignKey(configdefinition.ConfigClass)

    class Meta:
        unique_together = ("role", "config_class")
        ordering = ["role"]
        app_label = "core"
        db_table = 'core_roleconfigclassassignement'

    def __unicode__(self):
        return "Role:%s ConfigClass %s:" % (self.role.name,
                                            self.config_class.name)


class RoleDesConfigParamAssignment(models.Model):
    config_parameter = models.ForeignKey(configdefinition.ConfigClassParameter)
    role_description = models.ForeignKey(RoleDescription)

    class Meta:
        verbose_name = 'Role descr config class param assignment'
        unique_together = ("config_parameter", "role_description")
        ordering = ["role_description"]
        app_label = "core"
        db_table = 'core_roledesconfigparamassignment'

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_param_labels_by_description(cls, description_name):
        description = RoleDescription.get_by_name(description_name)
        return [c.config_parameter.name \
                    for c in cls.objects.filter(role_description=description)]

    def __unicode__(self):
        return ("RoleDescription: %s"
                " ConfigParam %s:") % (self.role_description.name,
                                       self.config_parameter.name)
