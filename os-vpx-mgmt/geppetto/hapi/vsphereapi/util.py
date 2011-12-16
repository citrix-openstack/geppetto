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

from geppetto.geppettolib import utils
from geppetto.hapi import interface
from geppetto.hapi.vsphereapi import vim_util


class DataStore(object):
    """DataStore Information."""

    def __init__(self, name=None, ref=None):
        """Initializes Name and Managed Object Reference of datastore."""
        self.name = name
        self.mor = ref


class DataCenter(object):
    """Datacenter Information."""

    def __init__(self, name=None, ref=None):
        """Initializes Managed Object Reference of datacenter."""
        self.name = name
        self.mor = ref


def get_host_ip():
    """Get the IP address of underlying host."""
    with file('/etc/openstack/vmware-url') as f:
        url = f.readline().strip()
        return url[url.find('=') + 1:]


def get_host_info(session):
    host_obj = session._call_method(vim_util, "get_objects",
                                    "HostSystem", ["name"])
    return host_obj[0].obj, host_obj[0].propSet[0].val


def get_by_uuid(session, vm_uuid):
    """Get reference to the VM with the uuid specified."""
    vms = session._call_method(vim_util, "get_objects",
                               "VirtualMachine", ["uuid"])
    for vm in vms:
        if vm.propSet[0].val == vm_uuid:
            return vm.obj
    return None


def get_vmconfig_change_spec(client_factory, params):
    """Builds the config spec to set virtual machine name in vmx file."""
    virtual_machine_config_spec = \
        client_factory.create('ns0:VirtualMachineConfigSpec')
    for key in params:
        if key == interface.VM.NAME:
            virtual_machine_config_spec.name = params[key]
        elif key == interface.VM.NAME_DESCRIPTION:
            virtual_machine_config_spec.annotation = params[key]
    return virtual_machine_config_spec


def set_config_params(session, vm_mor, params):
    """Set the virtual machine name and host ip in vmx file for
    the guest tools to pickup."""
    reconfigure_spec = \
            get_vmconfig_change_spec(session._get_vim().client.factory, params)
    reconfig_task = session._call_method(session._get_vim(),
                           "ReconfigVM_Task", vm_mor,
                           spec=reconfigure_spec)
    return wait_for_task(session, reconfig_task)


def _get_local_datastore(session):
    """Get the MOR to first local vmfs datastore."""
    default_datastore = None
    data_stores = session._call_method(vim_util, "get_objects",
                        "Datastore",
                        ["summary.type", "summary.name", "summary.datastore"])
    for ds in data_stores:
        ds_name = None
        ds_type = None
        for prop in ds.propSet:
            if prop.name == "summary.type":
                ds_type = prop.val
            elif prop.name == "summary.name":
                ds_name = prop.val
            elif prop.name == "summary.datastore":
                ds_mor = prop.val
        # Local storage identifier
        if ds_type == "VMFS":
            default_datastore = DataStore(ds_name, ds_mor)
            if default_datastore is not None:
                return default_datastore
    if default_datastore is None:
        raise exception.DataStoreNotFoundException()


def _get_default_folder(session):
    """Get default vmfolder of the datacenter in this ESX server."""
    dc_obj = session._call_method(vim_util, "get_objects",
                                    "Datacenter", ["vmFolder"])
    return dc_obj[0].propSet[0].val


def get_datacenter(session):
    """Get the datacenter name and the reference."""
    dc_obj = session._call_method(vim_util, "get_objects",
                                        "Datacenter", ["name"])
    return DataCenter(dc_obj[0].propSet[0].val, dc_obj[0].obj)


def get_resource_pool(session):
    """Get the first resource pool."""
    return session._call_method(vim_util, "get_objects",
                                    "ResourcePool")[0].obj


def create_vdisk_spec(client_factory, size_kb, controller_key,
                      file_path=None, unit_number=0):
    """
    Create specification for to attach already existing
    Virtual Disk to VM.
    """
    virtual_device_config = \
        client_factory.create('ns0:VirtualDeviceConfigSpec')
    virtual_device_config.operation = "add"
    if file_path is None:
        virtual_device_config.fileOperation = "create"

    disk_file_backing = \
        client_factory.create('ns0:VirtualDiskFlatVer2BackingInfo')
    disk_file_backing.diskMode = "persistent"
    disk_file_backing.thinProvisioned = False
    if file_path is not None:
        disk_file_backing.fileName = file_path
    else:
        disk_file_backing.fileName = ""

    connectable_spec = client_factory.create('ns0:VirtualDeviceConnectInfo')
    connectable_spec.startConnected = True
    connectable_spec.allowGuestControl = True
    connectable_spec.connected = True

    virtual_disk = client_factory.create('ns0:VirtualDisk')
    virtual_disk.backing = disk_file_backing
    virtual_disk.connectable = connectable_spec
    virtual_disk.key = -100
    virtual_disk.controllerKey = controller_key
    virtual_disk.unitNumber = unit_number
    if unit_number == 0:
        virtual_disk.capacityInKB = size_kb
    else:
        virtual_disk.capacityInKB = 1
    virtual_device_config.device = virtual_disk

    return virtual_device_config


def create_controller_spec(client_factory, key):
    """
    Create configuration specification for the LSI Logic Controller's addition
    to the VM.
    """
    #TODO: Consider different controllers (ide etc.) case of not Linux guest OS
    virtual_device_config = \
        client_factory.create('ns0:VirtualDeviceConfigSpec')
    virtual_device_config.operation = "add"
    virtual_lsi = \
        client_factory.create('ns0:VirtualLsiLogicController')
    virtual_lsi.key = key
    virtual_lsi.busNumber = 0
    virtual_lsi.hotAddRemove = True
    virtual_lsi.sharedBus = "noSharing"
    virtual_device_config.device = virtual_lsi
    return virtual_device_config


def get_vmdk_attach_spec(client_factory, size_kb, file_path,
                         adapter_type, unit):
    """Builds the vmdk attach config spec."""
    config_spec = client_factory.create('ns0:VirtualMachineConfigSpec')

    controller_key = -101
    controller_spec = create_controller_spec(client_factory, controller_key)
    vdisk_config_spec = create_vdisk_spec(client_factory, size_kb,
                                          controller_key, file_path, unit)
    device_config_spec = []
    device_config_spec.append(controller_spec)
    device_config_spec.append(vdisk_config_spec)

    config_spec.deviceChange = device_config_spec
    return config_spec


def get_vmdk_create_spec(client_factory, size_in_kb, adapter_type):
    """Builds the virtual disk create spec."""
    create_vmdk_spec = \
        client_factory.create('ns0:FileBackedVirtualDiskSpec')
    create_vmdk_spec.adapterType = adapter_type
    create_vmdk_spec.diskType = "thick"
    create_vmdk_spec.capacityKb = size_in_kb
    return create_vmdk_spec


def format_virtual_disk_path(datastore_name, path):
    """Build the datastore based path."""
    return "[%s] %s" % (datastore_name, path)


def wait_for_task(session, task):
    state = session._call_method(vim_util, "get_dynamic_property",
                                 task, "Task", "info.state")
    while state != 'success' and state != 'error':
        time.sleep(1)
        state = session._call_method(vim_util, "get_dynamic_property",
                                         task, "Task", "info.state")
    if state == 'success':
        return True
    else:
        return False


def get_disks_of_vm(session, vm_mor):
    disks = []
    device_info = session._call_method(vim_util, "get_dynamic_property",
                                   vm_mor, "VirtualMachine",
                                   "config.hardware.device")
    devices = device_info and device_info.VirtualDevice or []
    for device in devices:
        try:
            disks.append(device.backing.fileName)
        except:
            pass
    return disks


def get_disks_in_datastore(session, datastore, path=None):
    disks = []
    search_result = None
    if path:
        datastore_path = format_virtual_disk_path(datastore.name, path)
    else:
        datastore_path = "[" + datastore.name + "]"

    ds_browser_mor = session._call_method(vim_util, "get_dynamic_property",
                                        datastore.mor, "Datastore", "browser")
    search_spec = vim_util.build_vmdk_search_spec(
                                            session._get_vim().client.factory)
    search_task = session._call_method(session._get_vim(),
                                "SearchDatastore_Task",
                                ds_browser_mor,
                                datastorePath=datastore_path,
                               searchSpec=search_spec)
    completed = wait_for_task(session, search_task)
    task_result = session._call_method(vim_util,
                                            "get_dynamic_property",
                                            search_task,
                                            "Task", "info.result")
    try:
        if completed:
            search_result = task_result.file
            for file in search_result:
                disks.append(file.path)
    except:
        #If result of search is empty then task_result will not file property.
        pass

    return disks


def create_vif_spec(client_factory, network_name, mac_address):
    """
    Create a configuration specification to add a virtual network
    adapter to the Local VM.
    """
    network_spec = client_factory.create('ns0:VirtualDeviceConfigSpec')
    network_spec.operation = "add"

    # Specify the recommended card type for the VM based on the guest OS
    net_device = client_factory.create('ns0:VirtualPCNet32')
    #device_info = client_factory.create('ns0:Description')
    #device_info.summary = device

    backing = \
        client_factory.create('ns0:VirtualEthernetCardNetworkBackingInfo')
    backing.deviceName = network_name

    connectable_spec = \
        client_factory.create('ns0:VirtualDeviceConnectInfo')
    connectable_spec.startConnected = True
    connectable_spec.allowGuestControl = True
    connectable_spec.connected = True

    net_device.connectable = connectable_spec
    net_device.backing = backing
    #net_device.deviceInfo = device_info

    net_device.key = -99
    net_device.addressType = "manual"
    net_device.macAddress = mac_address
    net_device.wakeOnLanEnabled = True

    network_spec.device = net_device
    return network_spec


def delete_vif_spec(client_factory, key):
    """
    Create a configuration specification to remove a virtual network
    adapter attached to local VM.
    """
    network_spec = client_factory.create('ns0:VirtualDeviceConfigSpec')
    network_spec.operation = "remove"
    net_device = client_factory.create('ns0:VirtualPCNet32')
    net_device.key = key
    network_spec.device = net_device
    return network_spec


def find_device_by_label(session, vm_mor, device):
    """Returns device key if label matches specified device."""
    #NOTE: device  label is not reliably ordered. A sequence of deletion
    #followed by creation of devices manipulates the device label irrespective
    #of the order they are attached to VM
    hardware_info = session._call_method(vim_util, "get_dynamic_property",
                                vm_mor, "VirtualMachine", "config.hardware")
    for device in hardware_info.device:
        device_string = device.deviceInfo.label
        label_words = device_string.split(' ')
        if label_words[0] == "Network" and label_words[2] == device:
            return device.key
    return None


def find_network_by_key(session, vm_mor, key):
    hardware_info = session._call_method(vim_util, "get_dynamic_property",
                                vm_mor, "VirtualMachine", "config.hardware")
    for device in hardware_info.device:
        if device.key == key:
            return device.backing.deviceName
    return None


def get_max_seqnumber(disk_list, name_label, search_key):
    max_seqnumber = 0
    name_with_seqnumber = ''
    for full_name in disk_list:
        name_with_seqnumber = full_name.rsplit('__' + search_key, 1)[0]
        split_name = name_with_seqnumber.rsplit('__', 1)
        if split_name[0] == name_label and len(split_name) > 1:
            disk_custom_seqnumber = int(split_name[1])
            if max_seqnumber < disk_custom_seqnumber:
                max_seqnumber = disk_custom_seqnumber
    return max_seqnumber


def scan_scsi_bus(scsi_host='host0'):
    utils.execute("echo \"- - -\" > /sys/class/scsi_host/host0/scan")
