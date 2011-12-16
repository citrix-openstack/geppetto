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

from django.contrib import admin
from geppetto.geppettolib import puppet

from geppetto.tasks import task_utils

from geppetto.core.models import ConfigClass
from geppetto.core.models import ConfigClassParameterType
from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Group
from geppetto.core.models import GroupOverride
from geppetto.core.models import Host
from geppetto.core.models import Master
from geppetto.core.models import Node
from geppetto.core.models import NodeRoleAssignment
from geppetto.core.models import Override
from geppetto.core.models import Role
from geppetto.core.models import RoleDescription
from geppetto.core.models import RoleConfigClassAssignment
from geppetto.core.models import RoleDesConfigParamAssignment
from geppetto.core.views import service_proxy

logger = logging.getLogger('geppetto.core.views.admin_site')

admin.site.register(ConfigClassParameterType)
admin.site.register(Group)
admin.site.register(Host)
admin.site.register(Master)
admin.site.register(RoleDescription)


class ConfigClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
admin.site.register(ConfigClass, ConfigClassAdmin)


class ConfigClassParameterAdmin(admin.ModelAdmin):
    list_filter = ('config_class',)
    list_display = ('name', 'config_class', 'description')
admin.site.register(ConfigClassParameter, ConfigClassParameterAdmin)


class GroupOverrideAdmin(admin.ModelAdmin):
    list_filter = ('config_class_parameter',)
    list_display = ('group', 'config_class_parameter')
admin.site.register(GroupOverride, GroupOverrideAdmin)


class NodeAdmin(admin.ModelAdmin):
    list_display = ('fqdn', 'host', 'report_status',
                    'report_date', 'report_last_changed_date')
    actions = ['apply_changes']

    def apply_changes(self, request, queryset):
        node_fqdns = [node.fqdn for node in queryset]

        master_fqdn = puppet.PuppetNode().get_puppet_option('server')
        svc = service_proxy.create_proxy(master_fqdn, 8080,
                                         service_proxy.Proxy.Geppetto, 'v1')
        logger.debug('Applying configuration following node: %s' % node_fqdns)
        svc.Task.apply_changes(node_fqdns)

admin.site.register(Node, NodeAdmin)


class NodeRoleAssignmentAdmin(admin.ModelAdmin):
    list_filter = ('role',)
    list_display = ('node', 'role')
    actions = ['restart_services', 'delete_noderole_assignment']

    def get_actions(self, request):
        actions = super(NodeRoleAssignmentAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def restart_services(self, request, queryset):
        node_dict = {}
        for nodeRoleAssignment in queryset:
            if nodeRoleAssignment.node.fqdn not in node_dict:
                node_dict[nodeRoleAssignment.node.fqdn] = []
            node_dict[nodeRoleAssignment.node.fqdn].\
                          append(str(nodeRoleAssignment.role))

        master_fqdn = puppet.PuppetNode().get_puppet_option('server')
        svc = service_proxy.create_proxy(master_fqdn, 8080,
                                         service_proxy.Proxy.Geppetto, 'v1')
        for node in node_dict.keys():
            svc.Node.restart_services(node, node_dict[node])
    restart_services.short_description = ("Restart the services on the "
                                          "selected nodes")

    @task_utils.puppet_check
    @task_utils.puppet_kick
    def delete_noderole_assignment(self, request, queryset):

        def configuration_update(nodeRoleAssignment):
            """Ensure that if we delete a role from a VPX, we clean up files
            that have been touched by Puppet in the process and that the
            service roles being deleted are also stopped."""
            node_fqdn = None
            service_role = None
            try:
                role_name = nodeRoleAssignment.role.name
                logger.debug('Check init files for role %s' % role_name)
                if  role_name in InitFiles.mapping:
                    files = InitFiles.mapping[role_name]
                    node = Node.get_by_name(nodeRoleAssignment.node.fqdn)
                    logger.debug('%s will to be deleted from node %s' % (files,
                                                                         node))
                    # Add override
                    config_param = ConfigClassParameter.\
                                        get_by_name(ConfigClassParameter.\
                                                            VPX_ABSENT_FILES)
                    override = Override.get_by_node_and_param(node,
                                                              config_param)
                    if override:
                        logger.debug('Found override: %s' % override.value)
                        existing_files = eval(override.value)
                        for file in existing_files:
                            if file not in files:
                                files.append(file)
                            else:
                                logger.debug('File %s already target '
                                             'for deletion' % file)
                        override.value = str(files)
                    else:
                        logger.debug('Override not found by: '
                                     '%s %s' % (node, config_param))
                        override = Override.\
                            objects.create(node=node,
                                           config_class_parameter=config_param,
                                           value=str(files))
                    override.one_time_only = True
                    override.save()
                    logger.debug('Override saved.')
            except Exception, e:
                logger.error(e)

            if nodeRoleAssignment.enabled and \
               nodeRoleAssignment.role.service:
                logger.debug('NodeRoleAssignment being deleted: %s %s' %
                             (nodeRoleAssignment.node,
                              nodeRoleAssignment.role))
                node_fqdn = nodeRoleAssignment.node.fqdn
                service_role = nodeRoleAssignment.role.name
            return node_fqdn, service_role

        node_fqdns = []
        all_roles = []
        for nra in queryset:
            fqdn, role = configuration_update(nra)
            if fqdn and fqdn not in node_fqdns:
                node_fqdns.append(fqdn)
            if role and role not in all_roles:
                all_roles.append(role)
        queryset.delete()
        return {'node_fqdns': node_fqdns,
                'config_params': [ConfigClassParameter.VPX_ABSENT_FILES,
                                  ConfigClassParameter.VPX_RESTART_SERVICES, ],
                'roles': all_roles, }
    delete_noderole_assignment.short_description = ("Delete selected Node "
                                                    "Role Assignments")
admin.site.register(NodeRoleAssignment, NodeRoleAssignmentAdmin)


class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'internal', 'description')
admin.site.register(Role, RoleAdmin)


class RoleDesConfigParamAdmin(admin.ModelAdmin):
    list_filter = ('role_description', 'config_parameter')
    list_display = ('role_description', 'config_parameter')
admin.site.register(RoleDesConfigParamAssignment, RoleDesConfigParamAdmin)


class OverrideAdmin(admin.ModelAdmin):
    list_filter = ('config_class_parameter',)
    list_display = ('node', 'config_class_parameter', 'timestamp')
admin.site.register(Override, OverrideAdmin)


class RoleConfigClassAssignmentAdmin(admin.ModelAdmin):
    list_filter = ('role', 'config_class')
    list_display = ('role', 'config_class')
admin.site.register(RoleConfigClassAssignment, RoleConfigClassAssignmentAdmin)


class InitFiles():
    file_prefix = '/var/lib/geppetto'

    RING_BUILDER_FILE = '%s/%s' % (file_prefix, 'swift-ring-builder-init-run')
    IMAGE_CONTAINER_FILE = '%s/%s' % (file_prefix, 'image-container-init-run')
    OS_DASHBOARD_FILE = '%s/%s' % (file_prefix, 'openstack-dashboard-init-run')
    DATABASE_FILE = '%s/%s' % (file_prefix, 'database-init-run')
    NS_VPX_FILE = '%s/%s' % (file_prefix, 'ns-vpx-init-run')
    GLANCE_FILE = '%s/%s' % (file_prefix, 'glance-init-run')
    NOVA_VOLUME_FILE = '%s/%s' % (file_prefix, 'nova-volume-init-run')
    SWIFT_PROXY_FILE = '%s/%s' % (file_prefix, 'swift-swauth-prep-run')
    SWIFT_OBJECT_FILE = '%s/%s' % (file_prefix, 'swift-init-run')

    mapping = {Role.RING_BUILDER: [RING_BUILDER_FILE, ],
                Role.IMG_CONTAINER: [IMAGE_CONTAINER_FILE, ],
                Role.MYSQL: [DATABASE_FILE, ],
                Role.LBSERVICE: [NS_VPX_FILE, ],
                Role.GLANCE_API: [GLANCE_FILE, ],
                Role.NOVA_VOLUME: [NOVA_VOLUME_FILE, ],
                Role.SWIFT_PROXY: [SWIFT_PROXY_FILE, ],
                Role.SWIFT_OBJECT: [SWIFT_OBJECT_FILE, ],
                Role.OPENSTACK_DASHBOARD: [OS_DASHBOARD_FILE], }
