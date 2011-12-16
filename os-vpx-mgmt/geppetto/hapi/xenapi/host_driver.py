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


class XenAPIHostDriver(interface.Host):
    """Abstraction layer for Host operations."""

    def __init__(self, session):
        """Initializer."""
        super(interface.Host, self).__init__()
        self.session = session
        self.host = self.session.xenapi.host.get_all()[0]

    def get_properties(self, properties_list=None):
        props = {}
        rec = self.session.xenapi.host.get_record(self.host)
        if properties_list is None or 'metrics' in properties_list:
            metrics = \
                   self.session.xenapi.host_metrics.get_record(rec['metrics'])
        if properties_list is None or 'hostname' in properties_list:
            props['hostname'] = rec['hostname']
        if properties_list is None or 'address' in properties_list:
            props['address'] = rec['address']
        if properties_list is None or 'software_version' in properties_list:
            props['software_version'] = \
              {'product_version': rec['software_version']['product_version'], }
        if properties_list is None or 'cpu_info' in properties_list:
            props['cpu_info'] = \
                 {'cpu_count': rec['cpu_info']['cpu_count'], }
        if properties_list is None or 'metrics' in properties_list:
            props['metrics'] = \
                 {'memory_total': metrics['memory_total'],
                  'memory_free': metrics['memory_free'], }
        if properties_list is None or 'local_storage' in properties_list:
            storage_rec = None
            block_devices = rec["PBDs"]
            for device in block_devices:
                pdb_record = self.session.xenapi.PBD.get_record(device)
                sr_record = self.session.xenapi.SR.get_record(pdb_record["SR"])
                try:
                    if sr_record["other_config"]['i18n-key'] == \
                                                "local-storage":
                        storage_rec = sr_record
                        break
                except KeyError:
                    pass  # ignore an sr if it don't have an il8n-key
            props['local_storage'] = \
              {'physical_size': storage_rec['physical_size'],
               'physical_utilisation': storage_rec['physical_utilisation'], }
        return props

    def set_properties(self, **kwargs):
        """Set properties of underlying Host as per specified
        key value pair args."""
        pass

    def dump_info_to_file(self, file_name):
        """Dump all information about underlying host to specified file."""
        host_info_dict = self.get_properties()
        f = open(file_name, 'w')
        for key in host_info_dict:
            val = host_info_dict[key]
            if val is not None:
                f.write(key + "\t:\t" + str(val))
            else:
                f.write(key + "\t:\t" + str('None'))
            f.write("\n")
        f.close()
