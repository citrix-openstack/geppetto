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

import XenAPI

from geppetto.hapi import interface
from geppetto.hapi import exception
from geppetto.hapi import xenapi


class XenAPIStorageDriver(interface.Storage):
    """Storage abstraction layer.
    Class for Storage related operations."""

    def __init__(self, session, container=None):
        """Initializer."""
        super(interface.Storage, self).__init__()
        self.session = session
        self.vm = session.xenapi.VM.get_by_uuid(xenapi.get_vpx_uuid())
        self._set_default_container()

    def _set_default_container(self):
        """Set default storage container. Get reference of local or
        default storage repository."""
        pool_ref = self.session.xenapi.pool.get_all()[0]
        sr_ref = self.session.xenapi.pool.get_default_SR(pool_ref)

        if sr_ref is None:
            sr_refs = self.session.get_xenapi().SR.get_all()
            for sr_ref in sr_refs:
                sr_rec = self.session.get_xenapi().SR.get_record(sr_ref)
                if ('i18n-key' in sr_rec['other_config'] and
                    sr_rec['other_config']['i18n-key'] == 'local-storage'):
                    break
        self.container = sr_ref

    def create_virtualdisk(self, size=1024, name_label='OS_VPX_virtualdisk',
                           key=None):
        try:
            # add a default key to other-config
            other_config = {'os-vpx-extra': 'true'}
            if key:
                other_config[key] = 'true'
            vdi_ref = self.session.xenapi.VDI.create(
              {'name_label': name_label,
               'name_description': '',
               'SR': self.container,
               'virtual_size': str(size),
               'type': 'User',
               'sharable': False,
               'read_only': False,
               'xenstore_data': {},
               'other_config': other_config,
               'sm_config': {},
               'tags': []})
            return self.session.xenapi.VDI.get_uuid(vdi_ref)
        except XenAPI.Failure, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKCREATE_ERROR,
                                exception.exc_strs.STORAGE_DISKCREATE_ERROR,
                                inner_exception)

    def attach_virtualdisk(self, vdisk, **kwargs):
        for key in kwargs:
            if key == 'user_device':
                device = kwargs[key]
        vdi_ref = self.session.xenapi.VDI.get_by_uuid(vdisk)
        vdi_rec = self.session.xenapi.VDI.get_record(vdi_ref)
        vbd_ref = None
        try:
            vbd_ref = self.session.xenapi.VBD.create(
                       {'VM': self.vm,
                       'VDI': vdi_ref,
                       'userdevice': str(device),
                       'bootable': False,
                       'mode': 'RW',
                       'type': 'disk',
                       'unpluggable': True,
                       'empty': False,
                       'other_config': vdi_rec['other_config'],
                       'qos_algorithm_type': '',
                       'qos_algorithm_params': {},
                       'qos_supported_algorithms': [],
                       })
            self.session.xenapi.VBD.plug(vbd_ref)
        except XenAPI.Failure, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKATTACH_ERROR,
                                exception.exc_strs.STORAGE_DISKATTACH_ERROR,
                                inner_exception)

    def find_virtualdisk(self, search_key=None, **kwargs):
        try:
            return [vdi['uuid']
                    for vdi in
                        self.session.xenapi.VDI.get_all_records().itervalues()
                        if vdi['other_config'].get(search_key) == 'true']
        except XenAPI.Failure, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKFIND_ERROR,
                                exception.exc_strs.STORAGE_DISKFIND_ERROR,
                                inner_exception)

    def is_virtualdisk_in_use(self, vdisk_id):
        try:
            vdisk = self.session.xenapi.VDI.get_by_uuid(vdisk_id)
            allowed = self.session.xenapi.VDI.get_allowed_operations(vdisk)
            if 'destroy' in allowed:
                return False
            else:
                return True
        except XenAPI.Failure, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKFIND_ERROR,
                                exception.exc_strs.STORAGE_DISKFIND_ERROR,
                                inner_exception)

    def upload_dvd(self, glance_host=None, glance_port=None,
                   image_name=None, **kwargs):
        """Upload the mounted iso image on DVD drive to specified glance server
        with specified image name."""
        pass
