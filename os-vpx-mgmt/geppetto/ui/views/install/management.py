import logging

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from geppetto.ui.views import utils
from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Role

from geppetto.ui.forms.install import ChooseWorkerForm
from geppetto.ui.forms.install import SetupNetwork
from geppetto.ui.forms.install import ChooseNetworkTypeWithWorkerShown
from geppetto.ui.forms.install import DefineStaticNetwork

SESSION_NETWORK_WORKER = "GeppettoNetworkWorker"
NOVA_MANAGEMENT_TASK_ID = "geppetto-nova-management-task-id"
NOVA_API_TASK_ID = "geppetto-api-task-id"
AJAX_CONSOLE_PROXY_TASK_ID = "geppetto-ajax-console-proxy-task-id"
NOVA_SCHEDULER_TASK_ID = "geppetto-scheduler-task-id"

logger = logging.getLogger('geppetto.ui.views')
svc = utils.get_geppetto_web_service_client()


def _make_request(request, form, task_id, f):
    service = utils.get_geppetto_web_service_client()
    worker = form.get_clean_worker()
    request.session[task_id] = f(service, worker)


def _add_unused_workers(form, service, roles):
    node_fqdns = service.Node.exclude_by_roles(roles)
    node_details = service.Node.get_details(node_fqdns)
    form.add_workers_into_form(node_details)


@login_required
def setup_nova_api(request):
    text = "Please choose the node for the OpenStack Compute API. This" + \
            " worker will run both the OpenStack Compute API service and " + \
            "the OpenStack Dashboard."
    header = "OpenStack Compute API"

    def on_form_valid(form, service, roles):
        _make_request(request, form, NOVA_API_TASK_ID,
                      lambda s, w: s.Compute.add_apis([w], {}))
        return redirect('setup_scheduler')

    def update_form(form, service, roles):
        _add_unused_workers(form, service, [Role.NOVA_API])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


@login_required
def setup_scheduler(request):
    text = "Please choose the node for the OpenStack Compute Scheduler. " + \
            "This is used by the cloud controller to pick which Compute " + \
            "worker to use for new virtual machine instances."
    header = "OpenStack Compute Scheduler"

    def on_form_valid(form, service, roles):
        _make_request(request, form, NOVA_SCHEDULER_TASK_ID,
                      lambda s, w: s.Scheduling.add_workers([w], {}))
        return redirect('install_checklist')

    def update_form(form, service, roles):
        _add_unused_workers(form, service, [Role.NOVA_SCHEDULER])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


@login_required
def setup_nova_ajax_console_proxy(request):
    text = "Choose a node to run the OpenStack Text Console Proxy service."
    header = "OpenStack Text Console Proxy"

    def on_form_valid(form, service, roles):
        _make_request(request, form, AJAX_CONSOLE_PROXY_TASK_ID,
                      lambda s, w: s.Compute.add_ajax_console_proxies([w], {}))
        return redirect('install_checklist')

    def update_form(form, service, roles):
        _add_unused_workers(form, service, [Role.NOVA_AJAX_CONSOLE_PROXY])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


@login_required
def setup_network(request):
    text = "Please specify how virtual machine instance networking " \
           "should be managed. The networking mode will determine the " \
           "layer-2/layer-3  network model." \
           "Enabling HA networking will limit the effect of " \
           "failures to a single host, and reduce network traffic on " \
           "network workers."
    header = "OpenStack Network Configuration"

    def on_form_valid(form, service, roles):
        config = {}
        mode = form.cleaned_data["networking_mode"]
        multi_host = form.cleaned_data["multi_host"]
        config["MULTI_HOST"] = multi_host
        config["MODE"] = mode
        request.session["config"] = config

        next_header = "Settings for %s networking " \
                      "Virtual Interface" \
                      % (config["MODE"] == 'vlan' and
                         "vLAN" or "Flat DHCP")
        request.session['next_header'] = next_header

        redirect_to = 'setup_network_worker'
        if multi_host:
            redirect_to = (mode == 'flat') and 'setup_network_service' \
                                           or 'setup_network_public_vif'
        return redirect(redirect_to)

    def update_form(form, service, roles):
        #NOOP at the moment
        #Put current value of multi_host here!
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=SetupNetwork,
                                           update_form=update_form)(request)


@login_required
def setup_network_worker(request):
    text = "Please choose the node for the OpenStack Compute Network " + \
            "Worker. This is responsible for issuing IP addresses to " + \
            "virtual machine instances."
    header = "OpenStack Network Worker"

    def on_form_valid(form, service, roles):
        config = request.session["config"]
        if config["MODE"] == "vlan" or config["MODE"] == "flatdhcp":
            request.session[SESSION_NETWORK_WORKER] = form.get_clean_worker()
            request.session["config"] = config
            return redirect('setup_network_public_vif')
        else:
            #Nothing else to do!
            _make_request(request, form, NOVA_MANAGEMENT_TASK_ID,
                          lambda s, w: s.Network.add_workers([w], config))
        return redirect('setup_complete')

    def update_form(form, service, roles):
        _add_unused_workers(form, service, [Role.NOVA_NETWORK])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=ChooseWorkerForm,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


@login_required
def setup_network_public_vif(request):
    text = "Please specify the static network settings for the public " \
            "network on the OpenStack-VPX." \
            "Please note that these settings will not affect Openstack " \
            "networks which have already been created."
    header = "OpenStack Network Worker - %s" % request.session['next_header']

    def is_valid_interface(cleaned_data):
        iface = cleaned_data["device"]
        workers = []
        is_valid = True
        if SESSION_NETWORK_WORKER in request.session:
            workers.append(request.session[SESSION_NETWORK_WORKER])
        else:
            # No worker specified (we are in HA setup wizard)
            # Must ensure interface is not used on any compute worker!
            workers.extend(svc.Node.get_by_role(Role.NOVA_COMPUTE))
        for worker in workers:
            # Validate chosen interface (which is a bridge interface)
            worker_details = svc.Node.get_details([worker])
            group_overrides = worker_details.get('group_overrides', {})
            node_overrides = worker_details.get('node_overrides', {})
            public_if = node_overrides.get(
                            ConfigClassParameter.PUBLIC_INTERFACE,
                            group_overrides.get(
                                ConfigClassParameter.PUBLIC_INTERFACE,
                                svc.Config.get(
                                    ConfigClassParameter.PUBLIC_INTERFACE)))
            if iface == public_if:
                is_valid = False
                break

        err_msg = not is_valid and "Invalid interface. This interface is " \
                                   "already being used. Please choose " \
                                   "another interface from the list."

        return (is_valid, err_msg)

    def on_form_valid(form, service, roles):
        network_type = form.cleaned_data["network_type"]
        host_network = form.cleaned_data["host_network"]
        device = form.cleaned_data["device"]
        config = request.session["config"]
        config[ConfigClassParameter.GUEST_NETWORK_BRIDGE] = host_network
        config[ConfigClassParameter.BRIDGE_INTERFACE] = device
        config[ConfigClassParameter.GUEST_NW_VIF_MODE] = network_type
        request.session["config"] = config
        if network_type == "static":
            return redirect('setup_network_public_vif_static')
        else:
            return redirect('setup_network_service')

    def update_form(form, service, roles):
        form.validation_callback = is_valid_interface
        # In multi_host case we won't have a worker
        form.update_worker(request.session.get(SESSION_NETWORK_WORKER,
                                               'HA networking enabled'))
        # Don't allow static IP configuration in multi host mode
        # as it won't make ant sense
        if request.session["config"].get("MULTI_HOST", None) == True:
            form.update_choices((("dhcp", "DHCP"),
                                 ("noip", "No IP configuration")))

    #mode = request.session["config"].get("MODE", "vlan")
    #django_form = (mode == "vlan" and ChooseNetworkTypeWithWorkerShown
    #                              or ChooseNetworkWithWorkerShown)
    return utils.generate_form_request_handler(header, text,
                               on_form_valid=on_form_valid,
                               django_form=ChooseNetworkTypeWithWorkerShown,
                               update_form=update_form)(request)


@login_required
def setup_network_public_vif_static(request):
    text = "Please specify the static network settings for the public " \
            "network on the OpenStack-VPX."
    header = "OpenStack Network Worker - Static Network Settings"

    def on_form_valid(form, service, roles):
        ipaddress = form.cleaned_data["ip_address"]
        netmask = form.cleaned_data["netmask"]
        config = request.session["config"]
        config[ConfigClassParameter.GUEST_NW_VIF_IP] = ipaddress
        config[ConfigClassParameter.GUEST_NW_VIF_NETMASK] = netmask
        request.session["config"] = config
        return redirect('setup_network_service')

    def update_form(form, service, roles):
        form.update_worker(request.session.get(SESSION_NETWORK_WORKER,
                                               'You should not see me!'))

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=DefineStaticNetwork,
                                           update_form=update_form)(request)


@login_required
def setup_network_service(request):
    worker = request.session.get(SESSION_NETWORK_WORKER, None)
    config = request.session["config"]
    if worker:
        request.session[NOVA_MANAGEMENT_TASK_ID] = \
                        svc.Network.add_workers([worker], config)
    else:
        request.session[NOVA_MANAGEMENT_TASK_ID] = \
                        svc.Network.configure_ha(config)
    if SESSION_NETWORK_WORKER in request.session:
        del request.session[SESSION_NETWORK_WORKER]
    return redirect('setup_complete')


@login_required
def setup_complete(request):
    # TODO -- show progress??
    return redirect('install_checklist')
