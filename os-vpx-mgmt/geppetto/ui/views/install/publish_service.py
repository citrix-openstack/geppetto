import logging

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Role

from geppetto.ui.views import utils
from geppetto.ui.forms.install import DefineStaticNetwork
from geppetto.ui.forms.install import PublishService


SESSION_VAR_WORKER = "GeppettoPublishWorker"
SESSION_NETWORK_WORKER = "GeppettoNetworkWorker"

logger = logging.getLogger('geppetto.ui.views.install.publish_service')


@login_required
def publish(request):
    geppetto_service = utils.get_geppetto_web_service_client()
    text = "Please specify which XenServer network that is attached to " + \
            "your Public Network. This will be connected to device 2 of " + \
            "the selected os-vpx instance. Ensure you choose the correct " + \
            "network type for the public network. If you select static " + \
            "networking, you will prompted for the IP Address details on " + \
            "the next screen. This interface will also be used for " + \
            "binding floating ips."
    header = "Publish Service"

    def is_valid_interface(cleaned_data):
        iface = cleaned_data["device"]
        is_valid = True
        service = utils.get_geppetto_web_service_client()
        worker = cleaned_data["worker"]
        worker_details = service.Node.get_details([worker])
        group_overrides = worker_details.get('group_overrides', {})
        node_overrides = worker_details.get('node_overrides', {})
        # validate chosen interface (which is a public interface)
        bridge_if = node_overrides.get(
                        ConfigClassParameter.BRIDGE_INTERFACE,
                        group_overrides.get(
                            ConfigClassParameter.BRIDGE_INTERFACE,
                            service.Config.get(
                                ConfigClassParameter.BRIDGE_INTERFACE)))
        if iface == bridge_if:
            is_valid = False
        err_msg = not is_valid and "Invalid interface. This interface is " \
                                   "already being used. Please choose " \
                                   "another interface from the list."

        return (is_valid, err_msg)

    def on_form_valid(form, service, roles):
        network_type = form.cleaned_data["network_type"]
        host_network = form.cleaned_data["host_network"]
        device = form.cleaned_data["device"]
        worker = form.get_clean_worker()
        request.session[SESSION_VAR_WORKER] = worker
        overrides = {ConfigClassParameter.PUBLIC_NETWORK_BRIDGE: host_network,
                     ConfigClassParameter.PUBLIC_INTERFACE: device,
                     ConfigClassParameter.PUBLIC_NW_VIF_MODE: network_type}
        service.Config.add_node_overrides(worker, overrides)
        redirect_to = (network_type == 'dhcp') and 'install_checklist' \
                       or 'publish_service_static_network'
        return redirect(redirect_to)

    def update_form(form, service, roles):
        form.validation_callback = is_valid_interface
        # Don't allow empty IP configuration as it won't make any sense
        form.update_choices((("dhcp", "DHCP"),
                             ("static", "Static")),
                            initial='dhcp')
        form.set_initial_device(service.Config.
                                get(ConfigClassParameter.PUBLIC_INTERFACE))
        form.add_workers_into_form(_get_api_nodes(service))

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=PublishService,
                                           update_form=update_form,
                                           svc_proxy=geppetto_service)(request)


def _get_api_nodes(service):
    nodes = []
    nodes.extend(service.Node.get_by_role(Role.GLANCE_API))
    nodes.extend(service.Node.get_by_role(Role.NOVA_API))
    nodes.extend(service.Node.get_by_role(Role.SWIFT_PROXY))
    nodes.extend(service.Node.get_by_role(Role.NOVA_NETWORK))
    unique_nodes = frozenset(nodes)
    return service.Node.get_details(list(unique_nodes))


@login_required
def static_network(request):
    geppetto_service = utils.get_geppetto_web_service_client()
    text = "Please specify the static network settings for the VPX for " + \
            "your public network."
    header = "Publish Service - Static Network"

    def on_form_valid(form, service, roles):
        ipaddress = form.cleaned_data["ip_address"]
        netmask = form.cleaned_data["netmask"]
        worker = request.session[SESSION_VAR_WORKER]
        overrides = {ConfigClassParameter.PUBLIC_NW_VIF_IP: ipaddress,
                     ConfigClassParameter.PUBLIC_NW_VIF_NETMASK: netmask}
        service.Config.add_node_overrides(worker, overrides)
        request.session[SESSION_VAR_WORKER] = None
        return redirect('install_checklist')

    def update_form(form, service, roles):
        form.update_worker(request.session[SESSION_VAR_WORKER])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=DefineStaticNetwork,
                                           update_form=update_form,
                                           svc_proxy=geppetto_service)(request)
