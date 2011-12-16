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

import inspect

from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from DocXMLRPCServer import DocXMLRPCServer


def GenerateDjangoXMLRPCHandler(class_instance,
                                server_name="Citrix Service"):
    server = DocXMLRPCServer(("localhost", 0),
                             bind_and_activate=False,
                             allow_none=True)
    server.register_introspection_functions()
    server.register_instance(class_instance)
    server.set_server_name(server_name)
    server.set_server_title(server_name)
    server.set_server_documentation(class_instance.__doc__)

    def handler(request):
        if request.method == "POST":
            response = HttpResponse(content_type="application/xml")
            response.write(server._marshaled_dispatch(request.raw_post_data))
            return response
        elif request.method == "GET":
            response = HttpResponse(content_type="text/html")
            response.write(server.generate_html_documentation())
            return response
        else:
            return HttpResponseNotAllowed("GET", "POST")
    return handler


def GenerateDjangoXMLRPCHandler2(class_instance,
                                 server_name='Citrix Geppetto v0.1'):
    server = DocXMLRPCServer(("localhost", 0),
                             bind_and_activate=False, allow_none=True)
    server.register_introspection_functions()
    members = inspect.getmembers(class_instance)
    members.sort(key=lambda x: x[0])
    for member_name, member in members:
        if inspect.ismethod(member):
            if not member_name.startswith('_'):
                s = member_name.replace('___', '.')
                server.register_function(member, s)
    server.set_server_name(server_name)
    server.set_server_title(server_name)
    server.set_server_documentation(class_instance.__doc__)

    def handler(request):
        if request.method == "POST":
            response = HttpResponse(content_type="application/xml")
            response.write(server._marshaled_dispatch(request.raw_post_data))
            return response
        elif request.method == "GET":
            response = HttpResponse(content_type="text/html")
            response.write(server.generate_html_documentation())
            return response
        else:
            return HttpResponseNotAllowed("GET", "POST")
    return handler
