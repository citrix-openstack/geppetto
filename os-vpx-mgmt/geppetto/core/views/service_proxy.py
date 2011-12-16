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

import xmlrpclib


class Proxy:
    Geppetto, Classifier, Facter = range(3)

    details = {Geppetto: 'openstack/geppetto',
               Classifier: 'openstack/classifier',
               Facter: 'openstack/facter', }


def create_proxy(host_fqdn, port, proxy_type, version='', https=False):
    proto = https and 'https' or 'http'
    url = '%s://%s:%d/%s/%s' % (proto, host_fqdn, port,
                                Proxy.details[proxy_type], version)
    proxy = xmlrpclib.ServerProxy(url, allow_none=True)
    return proxy
