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
from geppetto.hapi.vsphereapi import vim_util


class VSphereAPINetworkDriver(interface.Network):
    """Network abstraction layer.
    Implementation for Network related operations on ESXi."""

    def __init__(self, session):
        """Initializer."""
        super(interface.Network, self).__init__()
        self.session = session
        self.vm = util.get_by_uuid(session, vsphereapi.get_vpx_uuid())

    def add_vif(self, network_identifier=None, **kwargs):
        """Add a virtual network interface to local VM.
        If mac_address is specified, it will be assigned to the interface.
        network_identifier must be specified.
        """
        #NOTE: User need to specify network name in UI form of publish services
        #TODO: Ensure the new VIF becomes eth2 inside VM otherwise need to
        #      find a way to discover device number
        mac_address = None
        for key in kwargs:
            if key == 'mac_address':
                mac_address = kwargs[key]
        if not network_identifier:
            exc_msg = exception.exc_strs.NETWORK_MISSING_PARAMETER % \
                                                    'network_identifier'
            raise exception.HAPIFailure(
                            exception.exc_codes.NETWORK_MISSING_PARAMETER,
                            exc_msg)

        client_factory = self.session._get_vim().client.factory
        nic_spec = util.create_vif_spec(client_factory,
                                                   network_identifier,
                                                   mac_address)
        device_config_spec = [nic_spec]
        vm_config_spec = client_factory.create('ns0:VirtualMachineConfigSpec')
        vm_config_spec.deviceChange = device_config_spec
        reconfig_task = self.session._call_method(self.session._get_vim(),
                           "ReconfigVM_Task", self.vm, spec=vm_config_spec)
        util.wait_for_task(self.session, reconfig_task)

    def find_vif(self, **kwargs):
        device = None
        for key in kwargs:
            if key == 'device':
                device = kwargs[key]
        if device == None:
            exc_msg = exception.exc_strs.NETWORK_MISSING_PARAMETER % 'device'
            raise exception.HAPIFailure(
                                exception.exc_codes.NETWORK_MISSING_PARAMETER,
                                exc_msg)
        #Search specified device by looking for deviceInfo.label
        #If found return key (VirtualDevice property) - class VirtualPCNet32
        return util.find_device_by_label(self.session, self.vm, device)

    def delete_vif(self, vif):
        try:
            key = vif
            client_factory = self.session._get_vim().client.factory
            delete_spec = util.delete_vif_spec(client_factory, key)

            reconfig_task = self.session._call_method(self.session._get_vim(),
                           "ReconfigVM_Task", self.vm, spec=vm_config_spec)
            util.wait_for_task(self.session, reconfig_task)

        #TODO: Add vSphere API Exception
        except Exception, inner_exception:
            raise exception.HAPIFailure(exception.exc_codes.NETWORK_VIF_ERROR,
                                        exception.exc_strs.NETWORK_VIF_ERROR,
                                        inner_exception)

    def get_network_by_name(self, network_name=None):
        """Get network by name. Returns network reference"""
        host_network_info = self.session._call_method(vim_util, "get_objects",
                                                "HostSystem", ["network"])
        network_list = host_network_info[0].propSet[0].val
        if not network_list:
            return None
        networks_mor = network_list.ManagedObjectReference
        networks = self.session._call_method(vim_util,
                           "get_properties_for_a_collection_of_objects",
                           "Network", networks_mor, ["summary.name"])
        for network in networks:
            if network.propSet[0].val == network_name:
                return network.obj
        return None

    def get_network_by_component(self, component_name=None):
        """Get network associated with specific network component (A bridge or
        a vSwitch or any backend component supporting virtual networking.
        Returns network reference."""
        pass

    def get_network_dict_by_vif(self, vif):
        """Returns name of network associated with specified vif."""
        return util.find_network_by_key(self.session, self.vm, vif)

    def get_network_dict_by_component(self, component):
        """Network name itself will be used to identify network.
        Mapping of network to vswitch is not 1-1. Hence can't judge
        network by component like vswitch."""
        return component

    def compare_networks(self, network_1, network_2):
        return network_1 == network_2
