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

import logging
import httplib
from xml.dom.minidom import parseString
from geppetto.core.views.xmlrpc import GenerateDjangoXMLRPCHandler

logger = logging.getLogger('geppetto.core.views.atlas_service')

LB_SERVICE_PORT = 4301
LB_SERVICE_VERS = 'v1'


class Service():
    """The service used by the LBaaS Web UI"""
    
    def create_load_balancer(self,
                             host,            # something like myhost
                             tenant_id,       # something like tenant_001
                             lb_name,         # something like lb_service_001
                             nodes,           # this is a list of dictionaries {address:string, port:int} 
                             port=80,         # this is the port used by the virtual load balancer
                             protocol='HTTP',
                             algorithm='ROUND_ROBIN'):
        """Returns list of dictionaries {address:str, id: str, ipVersion: str, type:str}"""
        # Prepare xml body
        data = _build_payload(lb_name,
                              nodes,
                              port,
                              protocol,
                              algorithm)
        # Prepare request params
        endpoint = '%s:%d' % (host, LB_SERVICE_PORT)
        ver = LB_SERVICE_VERS
        entity = 'loadbalancers'
        uri = '/%(ver)s/%(tenant_id)s/%(entity)s' % locals()
        headers = {"Content-type": "text/xml","Accept": "*/*"}
        # Make request and return response
        response = _make_request(endpoint, uri, 'POST', headers, data)
        if response['status'] == 202:
            return _return_lb_virtual_ips(response['body'])
        else:
            logging.error(response)
            raise Exception('Failure: %s, check logs for more information.' %
                            response['reason'])
    
    def read_load_balancer(self,
                           host,       # something like myhost
                           tenant_id,  # something like tenant_001
                           lb_id):     # something like lb_service_001
        """Returns a dictionary containing lb properties"""
        # Prepare request params
        endpoint = '%s:%d' % (host, LB_SERVICE_PORT)
        ver = LB_SERVICE_VERS
        entity = 'loadbalancers'
        uri = '/%(ver)s/%(tenant_id)s/%(entity)s/%(lb_id)s' % locals()
        headers = {"Content-type": "text/xml","Accept": "*/*"}
        # Make request and return response
        response = _make_request(endpoint, uri, 'GET', headers)
        if response['status'] == 200:
            return _return_lbs(response['body'])[0]
        else:
            logging.error(response)
            raise Exception('Failure: %s, check logs for more information.' %
                            response['reason'])
    
    def get_load_balancers(self,
                           host,       # something like myhost
                           tenant_id): # something like lb_service_001
        """Returns a list of lb properties dictionaries"""
        # Prepare request params
        endpoint = '%s:%d' % (host, LB_SERVICE_PORT)
        ver = LB_SERVICE_VERS
        entity = 'loadbalancers'
        uri = '/%(ver)s/%(tenant_id)s/%(entity)s' % locals()
        headers = {"Content-type": "text/xml","Accept": "*/*"}
        # Make request and return response
        response = _make_request(endpoint, uri, 'GET', headers)
        if response['status'] == 200:
            return _return_lbs(response['body'])
        else:
            logging.error(response)
            raise Exception('Failure: %s, check logs for more information.' %
                            response['reason'])
    
    def update_load_balancer(self,
                           host,       # something like myhost
                           tenant_id,  # something like tenant_001
                           lb_id,      # something like lb_service_001
                           **kwargs):  # named paramaters
        raise NotImplementedError()
    
    def delete_load_balancer(self,
                             host,        # something like myhost
                             tenant_id,   # something like tenant_001
                             lb_id):      # something like lb_service_001
        """Return true on success or false on failure"""
        endpoint = '%s:%d' % (host, LB_SERVICE_PORT)
        ver = LB_SERVICE_VERS
        entity = 'loadbalancers'
        uri = '/%(ver)s/%(tenant_id)s/%(entity)s/%(lb_id)s' % locals()
        # Make request and return response
        headers = {"Content-type": "text/xml","Accept": "*/*"}
        response = _make_request(endpoint, uri, 'DELETE', headers)
        if response['status'] == 202 or response['status'] == 404:
            return True
        else:
            logging.error(response)
            return False

def _return_lb_virtual_ips(response):
    xml_response = parseString(response)
    vips = []
    for node in xml_response.getElementsByTagName('virtualIp'):
        vips.append({'address': node.getAttribute('address'),
                     'id': node.getAttribute('id'),
                     'ipVersion': node.getAttribute('ipVersion'),
                     'type': node.getAttribute('type'),})
    return vips


def _return_lb_nodes(response):
    xml_response = parseString(response)
    nodes = []
    for element in xml_response.getElementsByTagName('node'):
        nodes.append({'address': element.getAttribute('address'),
                     'id': element.getAttribute('id'),
                     'port': element.getAttribute('port'),
                     'condition': element.getAttribute('condition'),
                     'status': element.getAttribute('status'),})
    return nodes


def _return_lbs(response):
    xml_response = parseString(response)
    lbs = []
    for element in xml_response.getElementsByTagName('loadBalancer'):
        props = {'name': element.getAttribute('name'),
                 'id': element.getAttribute('id'),
                 'status': element.getAttribute('status'),
                 'created': element.getElementsByTagName('created')[0].getAttribute('time'),
                 'updated': element.getElementsByTagName('updated')[0].getAttribute('time'),}
        if element.getAttribute('status') != 'DELETED':
            props['port'] = element.getAttribute('port')
            props['protocol'] = element.getAttribute('protocol')
            props['algorithm'] = element.getAttribute('algorithm')
            props['cluster'] = element.getElementsByTagName('cluster')[0].getAttribute('name')
            props['nodes'] = _return_lb_nodes(response)
            props['vips'] = _return_lb_virtual_ips(response)
        lbs.append(props)
    return lbs


def _build_payload(lb_name,
                   nodes,
                   port,
                   protocol,
                   algorithm):
    nodes_list = []
    for node in nodes:
        nodes_list.append((XML_NODE_SNIPPET % node))
    xml_nodes = ''.join(nodes_list)
    data_dict = {'lbname': lb_name,
                 'port': port,
                 'protocol': protocol,
                 'algorithm': algorithm,
                 'nodes': xml_nodes,}
    return XML_POST_PAYLOAD % data_dict


def _make_request(endpoint,
                  uri,
                  method='GET',
                  headers=None,
                  payload=None,):
    try: 
        connection = httplib.HTTPConnection(endpoint)
        if headers:
            connection.request(method, uri, payload, headers)
        else:
            connection.request(method, uri)
        response = connection.getresponse()
        status = response.status
        reason = response.reason
        body = response.read()
        response_dict = {'status': status, 
                         'reason': reason,
                         'body': body,}
        connection.close()
        return response_dict
    except Exception, e:
        logger.error('Failed to issue request: %(endpoint)s \
                      %(method)s %(uri)s %(payload)s %(headers)s' % locals())
        logger.error(e)


svc = GenerateDjangoXMLRPCHandler(Service())


XML_POST_PAYLOAD = \
"""
<loadBalancer xmlns="http://docs.openstack.org/loadbalancers/api/v1.0" name="%(lbname)s" port="%(port)s" protocol="%(protocol)s" algorithm="%(algorithm)s">
<virtualIps><virtualIp type="PUBLIC"/></virtualIps>
<nodes>
%(nodes)s</nodes>
</loadBalancer>
"""


XML_NODE_SNIPPET = \
"""<node address="%(address)s" port="%(port)d" condition="ENABLED" />
"""