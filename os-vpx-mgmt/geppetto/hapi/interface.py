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


from geppetto.hapi import config_util
from geppetto.hapi import exception


class Session(object):
    """Factory and session management class."""
    hv_session = None

    def __init__(self):
        self.Host = None
        self.Network = None
        self.Storage = None
        self.VM = None

    def login(self, username='root', password=None):
        raise NotImplementedError()

    def logout(self):
        raise NotImplementedError()

    @classmethod
    def createSession(cls, session_type=None):
        cls.hv_session = config_util.load_session(session_type)
        if cls.hv_session is None:
            raise exception.HAPIFailure(exception.exc_codes.\
                                        UNCLASSIFIED_SESSION_FAILURE,
                                        exception.exc_strs.\
                                        UNCLASSIFIED_SESSION_FAILURE)
        return cls.hv_session


class Host(object):
    """Host abstraction layer."""

    def get_properties(self, properties_list=None):
        """Get properties of underlying Host.

        Return dictionary of property names and values; e.g.

        { 'hostname': 'localhost',
          'address': '192.168.0.1',
          'software_version': {'product_version': 'x.y.z',},
          'cpu_info': {'cpu_count': '16',},
          'metrics': {'memory_total': '34349113344',
                      'memory_free': '28237160448',},
          'local_storage': {'physical_size': '65145929728',
                            'physical_utilisation: '4194304',}
        }
        """
        raise NotImplementedError()

    def set_properties(self, **kwargs):
        """Set properties of underlying Host as per specified key
        value pair args."""
        raise NotImplementedError()

    def dump_info_to_file(self, file_name):
        """Dump all information about underlying host to specified file."""
        raise NotImplementedError()


class Network(object):
    """Network abstraction layer."""

    def add_vif(self, network_identifier=None, **kwargs):
        """Add a virtual network interface to local VM.
        If mac_address is specified, it will be assigned to the interface.

        Return an (opaque) reference to the vif."""
        raise NotImplementedError()

    def delete_vif(self, vif):
        """Delete all virtual network interfaces attached to the local VM."""
        raise NotImplementedError()

    def find_vif(self, **kwargs):
        """Find the vif according to the search criteria.

        Return an (opaque) reference of the vif or None.
        """
        raise NotImplementedError()

    def get_network_by_component(self, component):
        """Get network associated with specific network component (A bridge or
        a vSwitch or any backend component supporting virtual networking.

        Return an (opaque) network reference."""
        raise NotImplementedError()

    def get_network_dict_by_vif(self, vif):
        """Return a dictionary of labels-values describing the properties
        of the network to which the vif is connected to"""
        raise NotImplementedError()

    def get_network_dict_by_component(self, component):
        """Return a dictionary of labels-values describing the properties
        of the network to which the component refers to"""
        raise NotImplementedError()

    def compare_networks(self, network_1, network_2):
        """Return true if the two network are identical.

        network_1 and network_2 are two dictionaries are returned by
        get_network_dict_by_vif"""
        raise NotImplementedError()


class Storage(object):
    """Storage abstraction layer."""

    def create_virtualdisk(self, size=1024, name_label='OS_VPX_virtualdisk',
                           key=None):
        """Create a virtual disk of specified size, with name_label.
        key is implementation specific: it is a way to identify the disk if
        multiple disks exists with the same name_label.

        Return an (opaque) identifier for the disk"""
        raise NotImplementedError()

    def attach_virtualdisk(self, vdisk, **kwargs):
        """Attach the specified virtual disk to local VM.
        If the underlying hypervisor does not support the operation, the
        implementation should pass silently; kwargs are implementation
        specific and can be used for extension."""
        raise NotImplementedError()

    def find_virtualdisk(self, search_key=None, **kwargs):
        """Finds all virtual disks in the host that match the specified key.

        Return list of (opaque) vdisk identifiers matching the key."""
        raise NotImplementedError()

    def is_virtualdisk_in_use(self, vdisk_id, **kwargs):
        """Checks if the specified virtual disk is in use.
        If the underlying hypervisor does not support the operation, the
        implementation should raise an exception.

        Return True if the virtual disk is in use; False otherwise."""
        raise NotImplementedError()

    def upload_dvd(self, glance_host=None, glance_port=None,
                   image_name=None, **kwargs):
        """Upload the mounted iso image on DVD drive to specified glance server
        with specified image name."""
        raise NotImplementedError()


class VM(object):
    """Abstraction layer for VM operations."""

    """Properties to be exposed. If a driver does not support
    a specific property a NotSupported Exception should be raised."""

    MEMORY = 'memory'
    NAME = 'name'
    POWER_STATE = 'power_state'
    NAME_DESCRIPTION = 'name_description'
    CPU = 'cpu'
    OS_BOOT_PARAMS = 'os_boot_params'
    TAGS = 'tags'

    def get_properties(self, property_list):
        """Get properties of local VM.
        Returns dictionary of property labels and values."""
        raise NotImplementedError()

    def set_properties(self, **kwargs):
        """Set properties of local VM as per specified key value pair args."""
        raise NotImplementedError()

    def clone(self, template_name=None, **kwargs):
        """Clone specified template to create new VM."""
        raise NotImplementedError()
