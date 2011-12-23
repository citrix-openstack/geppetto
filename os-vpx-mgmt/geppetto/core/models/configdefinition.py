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

import csv
import re

from django.db import models
from django.core import validators

from geppetto.core import exception_handler
from geppetto.core import exception_messages
from geppetto.core import Failure


class ConfigClass(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        app_label = "core"
        db_table = 'core_configclass'

    def get_params_dict(self):
        """Return dictionary of {param_label:param_value}"""
        return dict((param.name, param.default_value) \
                    for param in self.configclassparameter_set.all())

    def get_params(self):
        """Return dictionary of {param_label:param_value}"""
        return  self.configclassparameter_set.all()


class ConfigClassParameterType(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    validator_function = models.CharField(max_length=200)
    validator_kwargs = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        app_label = "core"
        db_table = 'core_configclassparametertype'

    def __unicode__(self):
        return self.name


class ConfigClassParameter(models.Model):
    # Nova params
    NETWORK_MANAGER = "NETWORK_MANAGER"
    MYSQL_HOST = "MYSQL_HOST"
    MYSQL_USER = "MYSQL_USER"
    MYSQL_PASS = "MYSQL_PASS"
    MYSQL_TYPE = "MYSQL_TYPE"
    RABBIT_HOST = "RABBIT_HOST"
    RABBIT_PORT = "RABBIT_PORT"
    RABBIT_USER = "RABBIT_USER"
    RABBIT_PASS = "RABBIT_PASS"
    USE_LOCAL_VOLUMES = "USE_LOCAL_VOLUMES"
    VOLUME_DISK_SIZE_GB = "VOLUME_DISK_SIZE_GB"
    VOLUME_DRIVER = "VOLUME_DRIVER"
    # Glance params
    GLANCE_HOSTNAME = "GLANCE_HOSTNAME"
    GLANCE_FILE_STORE_SIZE_GB = "GLANCE_FILE_STORE_SIZE_GB"
    GLANCE_STORE = "GLANCE_STORE"
    GLANCE_SWIFT_ADDRESS = "GLANCE_SWIFT_ADDRESS"
    # Swift params
    SWIFT_DISK_SIZE_GB = "SWIFT_DISK_SIZE_GB"
    SWIFT_NODES_IPS = "SWIFT_NODES_IPS"
    SWIFT_PROXY_ADDRESS = "SWIFT_PROXY_ADDRESS"
    SWIFT_HASH_PATH_SUFFIX = "SWIFT_HASH_PATH_SUFFIX"
    # LB Service params
    NS_VPX_HOST = "NS_VPX_HOST"
    NS_VPX_PASS = "NS_VPX_PASS"
    NS_VPX_PORT = "NS_VPX_PORT"
    NS_VPX_USER = "NS_VPX_USER"
    NS_VPX_VIPS = "NS_VPX_VIPS"
    # Geppetto params
    IMG_CONTAINER_OWNER = "IMG_CONTAINER_OWNER"
    IMG_CONTAINER_SIZE = "IMG_CONTAINER_SIZE"
    VPX_LABEL_PREFIX = "VPX_LABEL_PREFIX"
    VPX_LOGGING_COLLECTOR = "VPX_LOGGING_COLLECTOR"
    VPX_RESTART_SERVICES = "VPX_RESTART_SERVICES"
    VPX_ABSENT_FILES = "VPX_ABSENT_FILES"
    VPX_MASTER_DB_BACKEND = 'VPX_MASTER_DB_BACKEND'
    VPX_MASTER_DB_NAME = 'VPX_MASTER_DB_NAME'
    VPX_MASTER_DB_HOST = 'VPX_MASTER_DB_HOST'
    VPX_MASTER_DB_USER = 'VPX_MASTER_DB_USER'
    VPX_MASTER_DB_PASS = 'VPX_MASTER_DB_PASS'
    VPX_MASTER_QUEUE_HOST = 'VPX_MASTER_QUEUE_HOST'
    VPX_MASTER_QUEUE_USER = 'VPX_MASTER_QUEUE_USER'
    VPX_MASTER_QUEUE_PASS = 'VPX_MASTER_QUEUE_PASS'
    # Hypervisor params
    HAPI_DRIVER = "HAPI_DRIVER"
    HAPI_USER = "HAPI_USER"
    HAPI_PASS = "HAPI_PASS"
    # Networking params
    FIREWALL_DRIVER = "FIREWALL_DRIVER"
    GUEST_NETWORK_BRIDGE = "GUEST_NETWORK_BRIDGE"
    PUBLIC_NETWORK_BRIDGE = "PUBLIC_NETWORK_BRIDGE"
    BRIDGE_INTERFACE = "BRIDGE_INTERFACE"
    PUBLIC_INTERFACE = "PUBLIC_INTERFACE"
    GUEST_NW_VIF_MODE = "GUEST_NW_VIF_MODE"
    PUBLIC_NW_VIF_MODE = "PUBLIC_NW_VIF_MODE"
    GUEST_NW_VIF_IP = "GUEST_NW_VIF_IP"
    PUBLIC_NW_VIF_IP = "PUBLIC_NW_VIF_IP"
    GUEST_NW_VIF_NETMASK = "GUEST_NW_VIF_NETMASK"
    PUBLIC_NW_VIF_NETMASK = "PUBLIC_NW_VIF_NETMASK"
    COMPUTE_VLAN_INTERFACE = "COMPUTE_VLAN_INTERFACE"
    MULTI_HOST = "MULTI_HOST"
    FLAT_INJECTED = "FLAT_INJECTED"
    # Keystone params
    KEYSTONE_HOST = "KEYSTONE_HOST"
    KEYSTONE_SUPERUSER_NAME = "KEYSTONE_SUPERUSER_NAME"
    KEYSTONE_SUPERUSER_PASS = "KEYSTONE_SUPERUSER_PASS"
    KEYSTONE_SUPERUSER_TOKEN = "KEYSTONE_SUPERUSER_TOKEN"
    KEYSTONE_SUPERUSER_TENANT = "KEYSTONE_SUPERUSER_TENANT"
    # Compute-api params
    COMPUTE_API_HOST = "COMPUTE_API_HOST"
    # Host config params
    HOST_GUID = "HOST_GUID"

    config_class = models.ForeignKey(ConfigClass)
    name = models.CharField(max_length=50, unique=True, db_index=True)
    default_value = models.CharField(max_length=200)
    config_type = models.ForeignKey(ConfigClassParameterType,
                                    null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        app_label = "core"
        db_table = 'core_configclassparameter'

    def __unicode__(self):
        return self.name

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_by_name(cls, name):
        return cls.objects.get(name=name)

    @classmethod
    def set_config_parameter(cls, name, value):
        config = cls.get_by_name(name)
        config.validate(value)
        config.default_value = value
        config.save()

    @classmethod
    @exception_handler(exception_messages.not_found)
    def get_value_by_name(cls, name):
        return cls.objects.get(name=name).default_value

    @classmethod
    def get_values(cls):
        return [param.default_value for param in cls.objects.all()]

    @classmethod
    def get_names(cls):
        return [param.name for param in cls.objects.all()]

    @classmethod
    def get_config_dict(cls):
        return dict((param.name, param.default_value) \
                 for param in cls.objects.all())

    @classmethod
    def get_details_for_params(cls, param_labels):
        params = [cls.get_by_name(label) for label in param_labels]
        return dict((param.get_label(), param.get_details()) \
                                                for param in params)

    def get_label(self):
        return self.name

    def get_details(self):
        param_roles = [rel.role.name for rel in \
                       self.config_class.roleconfigclassassignment_set.all()]
        return {'applies-to': param_roles,
                'config-name': self.config_class.name,
                'config-description': self.config_class.description,
                'param-value': self.default_value,
                'param-description': self.description,
                'param-type': self.config_type.name, }

    def validate(self, value):
        # remove 'if self.config_type' once all parameters are under validation
        if self.config_type:
            validator_fun = self.config_type.validator_function
            validator_mod = 'geppetto.core.models.configdefinition'
            runtime = __import__(validator_mod, globals(), locals(),
                                                        [validator_fun], -1)
            # retrieve validator's kwargs if any
            validator_kwargs = {}
            if self.config_type.validator_kwargs:
                validator_kwargs = parse(self.config_type.validator_kwargs)

            getattr(runtime, validator_fun)(value, **validator_kwargs)


def get_default_settings(configs):
    return dict([((p.name, p.default_value)) \
                 for c in configs for p in c.get_params()])


def string_validator(value):
    """Everything is a string"""
    pass


def port_range_validator(value):
    """Throws a Failure exception if port is not valid"""
    try:
        port = int(value)
        if port < 1 or  port > 65535:
            raise Failure('port', 'port_range_validator',
                          '%s outside valid range' % value)
    except:
        raise Failure('port', 'port_range_validator',
                      '%s is not a valid integer' % value)


def boolean_validator(value):
    """Throws a Failure exception if value is not boolean"""
    if value not in ['True', 'true', 'False', 'false']:
        raise Failure(value, 'boolean_validator', 'is not valid')


@exception_handler(exception_messages.not_valid, 'Int')
def int_validator(value):
    """Throws a Failure exception if value is not int"""
    int(value)


@exception_handler(exception_messages.not_valid, 'Email')
def email_validator(value):
    """Throws a Failure exception if value is not a valid email"""
    validators.validate_email(value)


@exception_handler(exception_messages.not_valid, 'IP Address')
def ipv46address_validator(value):
    """Throws a Failure exception if value is not a valid IPv4 or
    IPv6 address"""
    validators.validate_ipv4_address(value)
    # TODO(am): add ipv6 validation when available in Django


def ipaddress_range_validator(value):
    """Throws a Failure exception if value is not a valid ip range"""
    try:
        ips = value.split('-')
        start = ips[0]
        end = ips[1]
        ipv46address_validator(start)
        ipv46address_validator(end)
    except:
        raise Failure(value, 'ipaddress_range_validator', 'is not a valid')


@exception_handler(exception_messages.not_valid, 'MAC Address')
def macaddress_validator(value):
    """Throws a Failure exception if value is not a valid mac address"""
    mac_re = re.compile(r'^([0-9a-fA-F]{2}([:-]?|$)){6}$')
    validators.RegexValidator(mac_re)(value)


@exception_handler(exception_messages.not_valid, 'URL')
def url_validator(value):
    """Throws a Failure exception if value is not a valid URL"""
    validators.URLValidator(verify_exists=False)(value)


@exception_handler(exception_messages.not_valid, 'FQDN')
def fqdn_validator(value):
    """Throws a Failure exception if value is a valid fqdn"""
    fqdn_re = re.compile(r'[-A-Za-z0-9.]+$')
    validators.RegexValidator(fqdn_re)(value)


def enum_validator(value, **kwargs):
    """Throws a Failure exception if value does not match
    any of the element in the enumeration"""
    if value not in kwargs:
        raise Failure(value, 'validate',
                      'permitted values -> "%s"' % kwargs.keys())


def parse(s):
    """Parse a comma-separated list of key=value pairs into a dictionary"""
    return dict(csv.reader([item],
                           delimiter='=',
                           quotechar="'").next()
                for item in csv.reader([s],
                                       delimiter=',',
                                       quotechar="'").next())
