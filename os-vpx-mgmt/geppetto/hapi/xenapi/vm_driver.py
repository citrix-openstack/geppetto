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

from geppetto.hapi import interface
from geppetto.hapi import exception
from geppetto.hapi import xenapi


class XenAPIVMDriver(interface.VM):
    """XenAPI implementation for VM operations."""

    def __init__(self, session=None, container=None, vm=None):
        """Initializer."""
        super(interface.VM, self).__init__()
        self.session = session
        self.vm = session.xenapi.VM.get_by_uuid(xenapi.get_vpx_uuid())
        self._mapping = {
                      interface.VM.MEMORY: 'memory_static_max',
                      interface.VM.NAME: 'name_label',
                      interface.VM.POWER_STATE: 'power_state',
                      interface.VM.NAME_DESCRIPTION: 'name_description',
                      interface.VM.CPU: 'VCPUs_at_startup',
                      interface.VM.OS_BOOT_PARAMS: 'PV_args',
                      interface.VM.TAGS: 'tags',
                      }

    def get_properties(self, property_list):
        vm_prop_dict = {}
        vm_rec = self.session.xenapi.VM.get_record(self.vm)
        for vm_property in property_list:
            try:
                vm_prop_dict[vm_property] = vm_rec[self._mapping[vm_property]]
            except:
                raise exception.HAPIFailure(
                                        exception.exc_codes.VM_PROPERTY_ERROR,
                                        exception.exc_strs.VM_PROPERTY_ERROR)
        return vm_prop_dict

    def set_properties(self, **kwargs):
        for key in kwargs:
            if key == interface.VM.NAME:
                self.session.xenapi.VM.set_name_label(self.vm,
                                                      kwargs[key])
            elif key == interface.VM.NAME_DESCRIPTION:
                self.session.xenapi.VM.set_name_description(self.vm,
                                                            kwargs[key])
            elif key == interface.VM.TAGS:
                self.session.xenapi.VM.set_tags(self.vm,
                                                kwargs[key])
            else:
                raise exception.HAPIFailure(
                                        exception.exc_codes.VM_PROPERTY_ERROR,
                                        exception.exc_strs.VM_PROPERTY_ERROR)

    def clone(self, template_name=None, **kwargs):
        pass
