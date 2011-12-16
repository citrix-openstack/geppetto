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


class XenAPINetworkDriver(interface.Network):
    """Network abstraction layer.
    Class for Network related operations."""

    def __init__(self, session):
        """Initializer."""
        super(interface.Network, self).__init__()
        self.session = session
        self.vm = session.xenapi.VM.get_by_uuid(xenapi.get_vpx_uuid())

    def add_vif(self, network_identifier=None, **kwargs):
        """Add a virtual network interface to local VM.

        device must be specified
        mac_address can be omitted"""
        bridge = network_identifier
        network_by_bridge = self.get_network_by_component(bridge)
        mac_address = device = ''
        for key in kwargs:
            if key == 'mac_address':
                mac_address = kwargs[key]
            elif key == 'device':
                device = kwargs[key]
        if device == '':
            exc_msg = exception.exc_strs.NETWORK_MISSING_PARAMETER % 'device'
            raise \
        exception.HAPIFailure(exception.exc_codes.NETWORK_MISSING_PARAMETER,
                              exc_msg)
        vif_ref = self.session.xenapi.VIF.create(
                        {'VM': self.vm,
                        'device': device,
                        'network': network_by_bridge,
                        'MAC': mac_address,
                        'MTU': "1500",
                        'other_config': {},
                        'qos_algorithm_type': "",
                        'qos_algorithm_params': {}})
        self.session.xenapi.VIF.plug(vif_ref)
        return self.session.xenapi.VIF.get_uuid(vif_ref)

    def delete_vif(self, vif):
        try:
            vif_ref = self.session.xenapi.VIF.get_by_uuid(vif['uuid'])
            self.session.xenapi.VIF.unplug(vif_ref)
            self.session.xenapi.VIF.destroy(vif_ref)
        except XenAPI.Failure, inner_exception:
            raise exception.HAPIFailure(exception.exc_codes.NETWORK_VIF_ERROR,
                                        exception.exc_strs.NETWORK_VIF_ERROR,
                                        inner_exception)

    def find_vif(self, **kwargs):
        device = None
        for key in kwargs:
            if key == 'device':
                device = kwargs[key]
        if device == None:
            exc_msg = exception.exc_strs.NETWORK_MISSING_PARAMETER % 'device'
            raise \
        exception.HAPIFailure(exception.exc_codes.NETWORK_MISSING_PARAMETER,
                              exc_msg)
        vif = [vif
           for vif in self.session.xenapi.VIF.get_all_records().itervalues()
           if ((vif['VM'] == self.vm) and (str(vif['device']) == device))]
        if len(vif) == 1:
            return vif[0]
        else:
            return None

    def get_network_by_component(self, component):
        bridge = component
        expr = 'field "name__label" = "%s" or ' \
               'field "bridge" = "%s"' % (bridge, bridge)
        networks = self.session.xenapi.network.get_all_records_where(expr)
        if len(networks) == 1:
            return networks.keys()[0]
        elif len(networks) > 1:
            raise Exception('Found non-unique network for bridge %s' % bridge)
        else:
            raise Exception('Found no network for bridge %s' % bridge)

    def get_network_dict_by_vif(self, vif):
        return self.session.xenapi.network.get_record(vif['network'])

    def get_network_dict_by_component(self, component):
        return \
            self.session.xenapi.network.get_record(
                                    self.get_network_by_component(component))

    def compare_networks(self, network_1, network_2):
        return network_1['uuid'] == network_2['uuid']
