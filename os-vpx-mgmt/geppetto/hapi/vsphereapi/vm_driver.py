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
from geppetto.hapi import vsphereapi
from geppetto.hapi.vsphereapi import util


class VSphereAPIVMDriver(interface.VM):
    """vSphere API implementation for VM operations."""

    def __init__(self, session=None, container=None, vm=None):
        """Initializer."""
        super(interface.VM, self).__init__()
        self.session = session
        self.vm = util.get_by_uuid(session, vsphereapi.get_vpx_uuid())
        self._mapping = {
                    interface.VM.NAME: 'summary.config.name',
                    interface.VM.POWER_STATE: 'summary.runtime.powerState',
                    interface.VM.MEMORY: 'summary.config.memorySizeMB',
                    interface.VM.CPU: 'summary.config.numCpu',
                    interface.VM.NAME_DESCRIPTION: 'summary.config.annotation',
                    #interface.VM.TAGS: 'summary.config.extraConfig'
                    }

    def get_properties(self, property_list):
        vm_prop_dict = {}
        for vm_property in property_list:
            #if self._mapping.has_key(vm_property) == False:
            #    raise NotImplementedError()
            try:
                if vm_property != self._mapping[vm_property]:
                    vm_prop_dict[vm_property] = self.session._call_method(\
                                vsphereapi.vim_util, "get_dynamic_property",
                                self.vm, "VirtualMachine",
                                self._mapping[vm_property])
            except:
                raise exception.HAPIFailure(
                                        exception.exc_codes.VM_PROPERTY_ERROR,
                                        exception.exc_strs.VM_PROPERTY_ERROR)
        return vm_prop_dict

    def set_properties(self, **kwargs):
        """Set properties of local VM as per specified key value pair args."""
        args = {}
        for key in kwargs:
            if key == interface.VM.NAME_DESCRIPTION:
                args[key] = kwargs[key]
            elif key == interface.VM.NAME:
                args[key] = kwargs[key]
            else:
                pass
        try:
            util.set_config_params(self.session, self.vm, args)
        except:
            raise exception.HAPIFailure(exception.exc_codes.VM_PROPERTY_ERROR,
                                        exception.exc_strs.VM_PROPERTY_ERROR)

    def clone(self, template_name=None, **kwargs):
        """Clone specified template to create new VM."""
        pass
