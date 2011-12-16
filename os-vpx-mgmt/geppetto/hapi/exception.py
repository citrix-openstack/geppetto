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


class exc_codes:
    # Generic Exceptions
    UNCLASSIFIED_UNKNOWN_ERROR = 0x0000
    UNCLASSIFIED_PASSWORD_UNCONFIGURED = 0x0001
    UNCLASSIFIED_SESSION_FAILURE = 0x0002
    UNCLASSIFIED_NOT_SUPPORTED = 0x0003
    UNCLASSIFIED_AUTHENTICATION_FAILURE = 0x0004
    UNCLASSIFIED_MISSING_VMWAREWSDL_FILES = 0x005
    # Host related Exceptions
    HOST_UNKNOWN_ERROR = 0x0100
    HOST_RESOURCE_NOTFOUND = 0x0101
    # Storage related Exceptions
    STORAGE_UNKNOWN_ERROR = 0x0200
    STORAGE_DATASTORE_NOTFOUND = 0x0201
    STORAGE_DISKCREATE_ERROR = 0x0202
    STORAGE_DISKATTACH_ERROR = 0x0203
    STORAGE_DISKFIND_ERROR = 0x0204
    # Network related Exceptions
    NETWORK_UNKNOWN_ERROR = 0x0300
    NETWORK_MISSING_PARAMETER = 0x0301
    NETWORK_VIF_ERROR = 0x0302
    # VM related Exceptions
    VM_UNKNOWN_ERROR = 0x0400
    VM_PROPERTY_ERROR = 0x0401
    # Add Exception codes accordingly


class exc_strs:
    # Do we need i18n?
    UNCLASSIFIED_UNKNOWN_ERROR = \
                'Unknown error. Please check inner exception if present.'
    UNCLASSIFIED_PASSWORD_UNCONFIGURED = 'The password is not set.'
    UNCLASSIFIED_SESSION_FAILURE = 'Unable to create session.'
    UNCLASSIFIED_NOT_SUPPORTED = 'This feature is not supported.'
    UNCLASSIFIED_AUTHENTICATION_FAILURE = 'Username or password invalid.'
    UNCLASSIFIED_MISSING_VMWAREWSDL_FILES = 'vSphere API wsdl files not found.'
    # Host related Exceptions
    HOST_UNKNOWN_ERROR = 'Unknown error while interacting with host.'
    HOST_RESOURCE_NOTFOUND = 'Resource could not be found.'
    # Storage related Exceptions
    STORAGE_UNKNOWN_ERROR = 'Unknown error while interacting with storage.'
    STORAGE_DATASTORE_NOTFOUND = \
                'Could not find any localdatastore on the host.'
    STORAGE_DISKCREATE_ERROR = 'Failed to create virtual disk.'
    STORAGE_DISKATTACH_ERROR = 'Failed to attach virtual disk.'
    STORAGE_DISKFIND_ERROR = 'Failed to find virtual disk.'
    # Network related Exceptions
    NETWORK_UNKNOWN_ERROR = 'Unknown error while interacting with network.'
    NETWORK_MISSING_PARAMETER = 'Missing parameter: %s.'
    NETWORK_VIF_ERROR = 'Unable to perform operation on vif.'
    # VM related Exceptions
    VM_UNKNOWN_ERROR = 'Unknown error while interacting with vm.'
    VM_PROPERTY_ERROR = 'Property not supported or not mistyped.'
    # Add Exception strings accordingly


class HAPIFailure(Exception):

    def __init__(self,
                 code=exc_strs.UNCLASSIFIED_UNKNOWN_ERROR,
                 message=exc_codes.UNCLASSIFIED_UNKNOWN_ERROR,
                 inner=None):
        self.code = code
        self.message = message
        self.inner = inner
