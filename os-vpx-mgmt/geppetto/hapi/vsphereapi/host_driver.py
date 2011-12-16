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

import os

from geppetto.hapi import interface
from geppetto.hapi import vsphereapi
from geppetto.hapi.vsphereapi import util


class VSphereAPIHostDriver(interface.Host):
    """Abstraction layer for Host operations."""

    def __init__(self, session):
        """Initializer."""
        super(interface.Host, self).__init__()
        self.session = session
        self.host, self.name = util.get_host_info(session)

    def get_properties(self, properties_list=None):
        props = {}
        if properties_list is None:
            memory_usage = 0
            metrics_dict = {}
            storage_dict = {}
            props['hostname'] = self.name
            props['address'] = util.get_host_ip()
            properties_list = []
            properties_list.append('config.product.version')
            properties_list.append('summary.hardware.numCpuCores')
            properties_list.append('summary.hardware.memorySize')
            properties_list.append('summary.quickStats.overallMemoryUsage')

            host_infos = self.session._call_method(vsphereapi.vim_util,
                                "get_objects", "HostSystem", properties_list)
            host_properties_dict = host_infos[0].propSet
            for property in host_properties_dict:
                if property.name == 'config.product.version':
                    props['software_version'] = \
                         {'product_version': property.val, }
                elif property.name == 'summary.hardware.numCpuCores':
                    props['cpu_info'] = \
                         {'cpu_count': property.val, }
                elif property.name == 'summary.hardware.memorySize':
                    metrics_dict['memory_total'] = property.val
                elif property.name == 'summary.quickStats.overallMemoryUsage':
                    memory_usage = property.val * 1024 * 1024

            metrics_dict['memory_free'] = \
                            metrics_dict['memory_total'] - memory_usage

            #TODO: Add up all local VMFS datastores on ESXi host
            datastore = util._get_local_datastore(self.session)
            storage_dict['physical_size'] = self.session._call_method(\
                            vsphereapi.vim_util, "get_dynamic_property",
                            datastore.mor, "Datastore", 'summary.capacity')
            datastore_freespace = self.session._call_method(\
                        vsphereapi.vim_util, "get_dynamic_property",
                        datastore.mor, "Datastore", 'summary.freeSpace')
            storage_dict['physical_utilisation'] = \
                            storage_dict['physical_size'] - datastore_freespace

            props['metrics'] = metrics_dict
            props['local_storage'] = storage_dict
        elif 'hostname' in properties_list or 'address' in properties_list:
            props['hostname'] = self.name
            props['address'] = util.get_host_ip()
        else:
            raise NotImplementedError()
        return props

    def set_properties(self, **kwargs):
        """Set properties of underlying Host as per specified
        key value pair args."""
        pass

    def dump_info_to_file(self, file_name=None):
        """Dump all information about underlying host to specified file."""
        if file_name is not None:
            if os.path.exists(file_name):
                f = open(file_name, "w")
        else:
            return
        host_info_dict = self.get_properties()
        for key in host_info_dict:
            f.write(key + "\t:\t" + str(host_info_dict[key]))
            f.write("\n")
