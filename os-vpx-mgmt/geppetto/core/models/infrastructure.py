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

import pickle
import string

import configdefinition
import roledependencies

from django.db import models
from django.core import validators

from geppetto.core import Failure
from geppetto.core import exception_handler
from geppetto.core import exception_messages
from geppetto.hapi.config_util import HOST_TYPES


class ReportStatus:
    Changed = 'c'
    Failed = 'f'
    Stable = 'u'
    Pending = '_'
    Disabled = '_'

    _Changed = 'changed'
    _Failed = 'failed'
    _Stable = 'stable'
    _Pending = 'pending'
    _Disabled = 'disabled'
    _Unchanged = 'unchanged'

    # the first three left-side values are what
    # come out Puppet Reports
    choices = {Changed: _Changed,
               Failed: _Failed,
               Stable: _Stable,
               Pending: _Pending,
               Disabled: _Disabled, }

    r_choices = {_Changed: Changed,
                 _Failed: Failed,
                 _Unchanged: Stable, }


class Host(models.Model):
    fqdn = models.CharField(max_length=200, unique=True, db_index=True)
    address = models.IPAddressField(blank=True)
    type = models.CharField(max_length=12, blank=True, choices=HOST_TYPES)

    class Meta:
        ordering = ["fqdn"]
        app_label = "core"
        db_table = 'core_host'

    def __unicode__(self):
        return self.fqdn

    @classmethod
    def create_or_update(cls, h_fqdn, h_address, h_type):
        host = None
        try:
            host = cls.objects.get(fqdn=h_fqdn)
            host.address = h_address
            host.type = h_type
            host.save()
        except Host.DoesNotExist:
            host = cls.objects.create(fqdn=h_fqdn,
                                      address=h_address,
                                      type=h_type)
        return host


class Group(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]
        app_label = "core"
        db_table = 'core_group'

    def __unicode__(self):
        return self.name

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_by_name(cls, name):
        return cls.objects.get(name=name)

    @classmethod
    def get_all_by_name(cls, name):
        return cls.objects.filter(name=name)

    @classmethod
    @exception_handler(exception_messages.non_unique)
    def create(cls, group_name):
        return cls.objects.create(name=group_name)

    @classmethod
    @exception_handler(exception_messages.not_found)
    def delete_by_name(cls, group_name):
        group = cls.get_by_name(group_name)
        group.delete()

    @exception_handler(exception_messages.not_found)
    def get_overrides_dict(self):
        return dict((o.config_class_parameter.name, o.value) \
                                for o in self.groupoverride_set.all())

    @exception_handler(exception_messages.not_found)
    def get_node_fqdns(self):
        return [n.fqdn for n in self.node_set.all()]


class Master(models.Model):
    fqdn = models.CharField(max_length=200, unique=True, db_index=True)
    promoted_date = models.DateTimeField('date promoted', auto_now_add=True)
    enabled = models.BooleanField()

    class Meta:
        ordering = ["fqdn"]
        app_label = "core"
        db_table = 'core_master'

    def __unicode__(self):
        return self.fqdn

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_infrastructure_master(cls, dns_suffix=None):
        """Return the master for the specific DNS zone"""
        for master in cls.objects.all():
            if dns_suffix is None:
                if master.enabled:
                    return master
            else:
                if string.find(master.fqdn, dns_suffix) and master.enabled:
                    return master
        raise RuntimeError("No Master in database")

    @classmethod
    def promote_node(cls, node_fqdn):
        # TODO(johngar) - add validation to ensure
        # there is only one enabled master at any time
        master = cls.get_infrastructure_master()
        master.fqdn = node_fqdn
        master.save()
        # Check that there is a remote syslog enabled for the cloud
        # if not, choose the master to be the one
        param_cls = configdefinition.ConfigClassParameter
        log_collector_label = param_cls.VPX_LOGGING_COLLECTOR
        if param_cls.get_value_by_name(log_collector_label) == 'localhost':
            param_cls.set_config_parameter(log_collector_label,
                                           node_fqdn)


class Node(models.Model):
    fqdn = models.CharField(max_length=200,
                            unique=True,
                            db_index=True,
                            verbose_name='VPX FQDN')
    joined_date = models.DateTimeField('date joined', auto_now_add=True)
    master = models.ForeignKey(Master)

    roles = models.ManyToManyField(roledependencies.Role,
                                   through='NodeRoleAssignment')

    group = models.ForeignKey(Group, null=True, blank=True,
                              on_delete=models.SET_NULL)

    facts = models.TextField(blank=True, editable=False)
    report = models.TextField(blank=True, editable=False)
    facts_list = models.TextField(blank=True)
    report_log = models.TextField(blank=True)
    report_date = models.DateTimeField(blank=True,
                                       null=True,
                                       verbose_name="Date of last report")
    report_last_changed_date = \
                models.DateTimeField(blank=True,
                                     null=True,
                                     verbose_name="Date of last report change")
    report_status = models.CharField(max_length=1,
                                     choices=ReportStatus.choices.items(),
                                     blank=True)
    host = models.ForeignKey(Host, null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["fqdn"]
        app_label = "core"
        db_table = 'core_node'

    def __unicode__(self):
        return self.fqdn

    @classmethod
    @exception_handler(exception_messages.non_unique)
    def create(cls, node_fqdn):
        return cls.objects.create(fqdn=node_fqdn,
                                  master=Master.get_infrastructure_master())

    def disable(self):
        self.enabled = False
        self.set_report_status(ReportStatus.Disabled)
        self.save()

    @classmethod
    def get_all_by_rolename(cls, role_name):
        return cls.objects.filter(roles__name=role_name,
                                  enabled=True)

    def get_details(self):
        d = dict(self.__dict__)
        d['master_fqdn'] = self.master.fqdn
        d['host_fqdn'] = self.host is None and \
                          self.get_fact('host_fqdn') or self.host.fqdn
        d['host_ipaddress'] = self.host is None and \
                          self.get_fact('host_ipaddress') or self.host.address
        d['host_virt'] = self.host is None and \
                          self.get_fact('host_type') or self.host.type
        d['management_ip'] = self.get_fact('ipaddress_eth1')
        d['hostnetwork_ip'] = self.get_fact('ipaddress_eth0')
        d['interfaces'] = self.get_fact('interfaces')
        d['roles'] = self.get_roles()
        d['group_overrides'] = self.get_group_overrides_dict()
        d['node_overrides'] = self.get_overrides_dict()
        # Remove stuff that's not needed
        if '_master_cache' in d:
            del d['_master_cache']
        del d['facts']
        del d['facts_list']
        del d['report']
        del d['_state']
        del d['report_log']
        return d

    @classmethod
    def get_fqdns(cls):
        return [node.fqdn for node in cls.objects.filter(enabled=True)]

    @classmethod
    def get_fqdns_by_role(cls, role, is_service=True, is_internal=False):
        return [node.fqdn for node in cls.objects.\
                                            filter(roles__name=role,
                                            roles__service=is_service,
                                            roles__internal=is_internal,
                                            enabled=True)]

    @classmethod
    def get_fqdns_by_roles(cls, roles):
        return [node.fqdn \
                for node in cls.objects.filter(roles__name__in=roles,
                                               enabled=True).distinct()]

    @classmethod
    def get_fqdns_excluded_by_roles(cls, roles):
        return [node.fqdn \
                for node in cls.objects.exclude(roles__name__in=roles,
                                                enabled=True).distinct()]

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_by_name(cls, node_fqdn):
        node = cls.objects.get(fqdn=node_fqdn)
        if not node.enabled:
            raise validators.ValidationError('Node not enabled')
        return node

    @classmethod
    def safe_get_by_name(cls, node_fqdn):
        try:
            return cls.get_by_name(node_fqdn)
        except Failure:
            return None

    def get_roles(self):
        return [rel.role for rel in self.noderoleassignment_set.all()]

    def get_role_assignments(self):
            return self.noderoleassignment_set.all()

    def delete_roles(self, role_exceptions=roledependencies.DEFAULT_ROLES):
        return self.noderoleassignment_set.\
                            exclude(role__name__in=role_exceptions).delete()

    def get_enabled_services(self):
        return [rel.role.name
                for rel in self.noderoleassignment_set.\
                            filter(enabled__exact=True) if rel.role.service]

    def get_group(self):
        return self.group

    @exception_handler(exception_messages.non_unique)
    def set_group(self, group):
        self.group = group
        self.save()

    def unset_group(self, group):
        # Signature is for supporting multiple
        # group-association when is added
        if self.group:
            self.group = None
            self.save()

    def get_overrides(self):
        return self.override_set.all()

    def delete_overrides(self):
        return self.override_set.all().delete()

    def get_overrides_dict(self):
        return dict((o.config_class_parameter.name, o.value) \
                                            for o in self.override_set.all())

    def get_group_overrides(self):
        return self.group.groupoverride_set.all()

    def get_group_overrides_dict(self):
        _dict = {}
        if self.group:
            _dict = self.group.get_overrides_dict()
        return _dict

    def get_fact(self, fact_name):
        try:
            pickled_facts = pickle.loads(str(self.facts))
            if fact_name in pickled_facts:
                return pickled_facts[fact_name]
        except:
            pass
        # Not reported or problem parsing facts
        return 'N/A'

    def set_report(self, report_details):
        self.report = report_details['pickled_report']
        self.report_date = report_details['report_time']
        if report_details['status_code'] != ReportStatus.Failed:
            self.report_status = report_details['status_code']
        else:
            self.report_status = ReportStatus.Pending
        self.report_log = report_details['report_log']
        if self.report_status != ReportStatus.Stable:
            self.report_last_changed_date = report_details['report_time']

    def set_facts(self, facts_details):
        self.facts = facts_details['pickled_facts']
        self.facts_list = facts_details['pretty_facts']
        facts_dict = facts_details['facts_obj']
        auth_status = 'host_password_status' in facts_dict \
                            and facts_dict['host_password_status'] or None
        if auth_status == 'SET' and 'host_fqdn' in facts_dict and \
                                    'host_ip' in facts_dict and \
                                    'host_type' in facts_dict:
            host_fqdn = facts_dict['host_fqdn']
            host_address = facts_dict['host_ip']
            host_type = facts_dict['host_type']
        else:
            host_fqdn = host_address = host_type = ''
        self.host = Host.create_or_update(host_fqdn, host_address, host_type)

    def is_authenticated(self):
        auth_status = self.get_fact('host_password_status')
        if auth_status == 'N/A' or auth_status == 'UNSET':
            return None     # unauthenticated
        elif auth_status == 'SET':
            return True     # authenticated
        elif auth_status == 'WRONG':
            return False    # bad credentials

    def get_report_status(self):
        return self.report_status

    @exception_handler(exception_messages.not_valid)
    def set_report_status(self, status):
        if status in ReportStatus.choices.keys():
            self.report_status = status
            self.save()
        else:
            raise validators.ValidationError('Invalid Report Status')

    def update_group(self, group):
        self.group = group
        self.save()
