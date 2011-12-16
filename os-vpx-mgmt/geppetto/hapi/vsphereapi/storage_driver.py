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

import time


from geppetto.hapi import interface
from geppetto.hapi import exception
from geppetto.hapi import vsphereapi
from geppetto.hapi.vsphereapi import util


class VSphereAPIStorageDriver(interface.Storage):
    """Storage abstraction layer.
    Class for Storage related operations on ESXi"""

    def __init__(self, session, container=None):
        """Initializer."""
        super(interface.Storage, self).__init__()
        self.session = session
        self.vm = util.get_by_uuid(session, vsphereapi.get_vpx_uuid())
        self.adapter_type = 'lsiLogic'
        self._set_default_container()
        self._set_default_folder()

    def _set_default_container(self):
        """Get MOR of first local vmfs datastore."""
        self.container = util._get_local_datastore(self.session)

    def _set_default_folder(self):
        """Get MOR of default vmfolder of the datacenter."""
        self.folder = util._get_default_folder(self.session)

    def create_virtualdisk(self, size=1024, name_label='OS_VPX_virtualdisk',
                           key=None):
        """Create virtual disk of specified size with name as
        '[datastore1] name_label.__key__.vmdk'.
        TODO: We might want to create sub folders with name 'key' to
        maintain name_label and key separate as entities."""
        if not key:
            key = "geppetto-openstack"
        #Retrieve all virtual disks matching the specified key
        vmdk_list = self.find_virtualdisk(key)

        new_seqnumber = util.get_max_seqnumber(vmdk_list, name_label,
                                                    key)
        new_diskname = name_label + '__' + str(new_seqnumber + 1) \
                                  + '__' + key + '__.vmdk'
        size_kb = int(size) / 1024
        vmdk_create_spec = util.get_vmdk_create_spec(
                                        self.session._get_vim().client.factory,
                                        size_kb, self.adapter_type)

        datastore_name = self.container.name
        datacenter_obj = util.get_datacenter(self.session)
        virtual_disk_path = util.format_virtual_disk_path(datastore_name,
                                                          new_diskname)
        try:
            create_task = self.session._call_method(
                            self.session._get_vim(),
                            "CreateVirtualDisk_Task",
                            self.session.service_content.virtualDiskManager,
                            name=virtual_disk_path,
                            datacenter=datacenter_obj.mor,
                            spec=vmdk_create_spec)
            #Wait for the asynchronous task to complete
            is_created = util.wait_for_task(self.session,
                                            create_task)
            if is_created:
                return virtual_disk_path
            else:
                raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKCREATE_ERROR,
                                exception.exc_strs.STORAGE_DISKCREATE_ERROR,
                                None)
        #TODO: Add VSphereAPI.Failure instead of Exception
        except Exception, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKCREATE_ERROR,
                                exception.exc_strs.STORAGE_DISKCREATE_ERROR,
                                inner_exception)

    def attach_virtualdisk(self, vdisk, **kwargs):
        """Attach specified virtual disk to local VM."""
        size_kb = 1024
        for key in kwargs:
            if key == 'size':
                size_kb = kwargs[key] * 1024 * 1024  # size will be in GB

        if vdisk[0] == '[':
            vdisk_path = vdisk
        else:
            vdisk_path = util.format_virtual_disk_path(self.container.name,
                                                       vdisk)
        disks = util.get_disks_of_vm(self.session, self.vm)
        unit_number = len(disks)
        #Avoid clash with SCSI Controller that sits on it's own bus.
        if unit_number >= 7:
            unit_number = unit_number + 1
        try:
            attach_config_spec = util.get_vmdk_attach_spec(
                                        self.session._get_vim().client.factory,
                                        size_kb, vdisk_path, self.adapter_type,
                                        unit_number)
            #("Reconfiguring VM instance %s to attach the disk %s")
            #                                         % (self.vm, vdisk_path)
            reconfig_task = self.session._call_method(
                               self.session._get_vim(),
                               "ReconfigVM_Task", self.vm,
                               spec=attach_config_spec)
            util.wait_for_task(self.session, reconfig_task)
            #NOTE:Forced scsi_host bus scan to hook up to the hot added disk
            util.scan_scsi_bus()
            time.sleep(2)

        #TODO: Add VSphereAPI.Failure type instead of Exception
        except Exception, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKATTACH_ERROR,
                                exception.exc_strs.STORAGE_DISKATTACH_ERROR,
                                inner_exception)

    def find_virtualdisk(self, search_key=None, **kwargs):
        """Finds virtual disk in the host that matches the specified key.
        Returns virtual disk name."""
        disk_list = []
        try:
            vmdk_list = util.get_disks_in_datastore(self.session,
                                                    self.container)
            for full_name in vmdk_list:

                split_full_name = full_name.rsplit('__' + search_key + '__.',
                                                   1)
                if len(split_full_name) > 1:
                    name_with_seqnumber = split_full_name[0]
                    split_name = name_with_seqnumber.rsplit('__', 1)
                    if len(split_name) > 1:
                        disk_list.append(full_name)
            return disk_list
        except Exception, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKFIND_ERROR,
                                exception.exc_strs.STORAGE_DISKFIND_ERROR,
                                inner_exception)

    def is_virtualdisk_in_use(self, vdisk_id):
        """Checks if the specified virtual disk is attached
        to local VM or not. Returns True if the virtual disk is attached."""
        vmdk_name = util.format_virtual_disk_path(self.container.name,
                                                  vdisk_id)
        try:
            disks = util.get_disks_of_vm(self.session, self.vm)
            for disk in disks:
                if disk == vmdk_name:
                    return True
            return False

        except Exception, inner_exception:
            raise exception.HAPIFailure(
                                exception.exc_codes.STORAGE_DISKFIND_ERROR,
                                exception.exc_strs.STORAGE_DISKFIND_ERROR,
                                inner_exception)

    def upload_dvd(self, glance_host=None, glance_port=None,
                   image_name=None, **kwargs):
        """Upload the mounted iso image on DVD drive to specified glance server
        with specified image name."""
        pass
