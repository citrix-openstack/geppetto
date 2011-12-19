import logging
import pprint

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.ui.views import utils
from geppetto.ui.forms.lbaas import ConfigureLBaaSForm
from geppetto.ui.forms.lbaas import LoadBalancerSelectVMs
from geppetto.ui.forms.lbaas import LoadBalancerURL
from geppetto.ui.forms.lbaas import LoadBalancerAction
from geppetto.ui.forms.lbaas import LoadBalancerList
from geppetto.ui.forms.lbaas import LoadBalancerDelete
from geppetto.ui.forms.lbaas import LBaaSInfoForm
from geppetto.core.models import Role, ConfigClassParameter

svc = utils.get_geppetto_web_service_client()
logger = logging.getLogger('geppetto.ui.views')


@login_required
def configure_lbaas(request):
    text = ("Please choose a VPX which you want to deploy the LB Service "
            "on. Also, insert the IP address of the NetScaler you are "
            "using and the range of IP addresses which the LB Service is "
            "going to allocate (e.g. 192.168.1.50-192.168.1.100).")
    header = "LBaaS Setup - NetScaler Integration"

    def on_form_valid(form, service, roles):
        config = {ConfigClassParameter.\
                    NS_VPX_HOST: form.cleaned_data['netscaler'],
                  ConfigClassParameter.\
                    NS_VPX_VIPS: form.cleaned_data['virtual_ips'],
                  ConfigClassParameter.\
                    VPX_LABEL_PREFIX: 'Load Balancer'}
        # FIXME(armandomi): track the task
        service.LBaaS.add_api(form.cleaned_data["worker"], config)
        return redirect('install_checklist')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.LBSERVICE])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=ConfigureLBaaSForm,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


SESSION_LB_TENANT = "GeppettoLbTenat"
SESSION_LB_URL = "GeppettoLbURL"
SESSION_LB_LIST = "GeppettoLbList"


@login_required
def lbservice(request):
    dummy_tenants = ["Administrator"]
    text = "Please select what Load Balancer operation you require:"
    header = "Load Balancer Service"

    def on_form_valid(form, service, roles):
        request.session[SESSION_LB_TENANT] = form.cleaned_data["tenant"]
        operation = form.cleaned_data["operation"]
        if operation == "list":
            return redirect('lbservice_list')
        if operation == "add":
            return redirect('lbservice_select_vms')
        if operation == "delete":
            return redirect('lbservice_delete')

    def update_form(form, service, roles):
        form.add_tenants_into_form(dummy_tenants)
        # TODO - need real list of tenants...

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=LoadBalancerAction,
                                           update_form=update_form)(request)


@login_required
def lbservice_select_vms(request):
    text = "Please specify a friendly name for the load balancer and then" + \
            " choose which of your VM instances you wish to load balance."
    header = "Publish Service - Select VMs"
    if request.session[SESSION_LB_TENANT] == None:
        return redirect('lbservice')

    def on_form_valid(form, service, roles):
        tenant = request.session[SESSION_LB_TENANT]
        lb_name = form.cleaned_data["friendly_name"]
        port = form.cleaned_data["port"]
        nodes = []
        for node in form.cleaned_data["virtual_machines"]:
            nodes.append({'address': node, 'port': int(port)})
        atlas_service = utils.get_atlas_client()
        try:
            lb_result = atlas_service.create_load_balancer(\
                        utils.get_lbaas_host(), tenant, lb_name, nodes, port)
            request.session[SESSION_LB_URL] = "http://%s:%s/" % (\
                                              lb_result[0]["address"], port)
            return redirect('lbservice_finish')
        except Exception, e:
            logger.error(e)
            request.session['LBAAS_LAST_ERROR'] = e
            return redirect('lbservice_info')
        finally:
            request.session[SESSION_LB_TENANT] = None

    def update_form(form, service, roles):
        form.add_vms_into_form(utils.get_ec2_client().get_instances())

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=LoadBalancerSelectVMs,
                                           update_form=update_form)(request)


@login_required
def lbservice_finish(request):
    text = "Your load balancer has now been setup. Below is the load " + \
                "balanced URL."
    header = "Publish Service - Added"
    if request.session[SESSION_LB_URL] == None:
        return redirect('lbservice')

    def on_form_valid(form, service, roles):
        request.session[SESSION_LB_URL] = None
        return redirect('install_checklist')

    def update_form(form, service, roles):
        form.update_url(request.session[SESSION_LB_URL])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=LoadBalancerURL,
                                           update_form=update_form)(request)


@login_required
def lbservice_list(request):
    text = "Here is a list of your current load balancers and their details:"
    header = "Load Balance Service - List"
    if request.session[SESSION_LB_TENANT] == None:
        return redirect('lbservice')

    def on_form_valid(form, service, roles):
        request.session[SESSION_LB_TENANT] = None
        return redirect('install_checklist')

    def update_form(form, service, roles):
        host = utils.get_lbaas_host()
        tenant = request.session[SESSION_LB_TENANT]
        try:
            atlas = utils.get_atlas_client()
            lb_list = atlas.get_load_balancers(host, tenant)
            form.update_list(pprint.pformat(lb_list, 2, 2, 2))
        except Exception, e:
            logger.error(e)
            request.session['LBAAS_LAST_ERROR'] = e
            return redirect('lbservice_info')
    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=LoadBalancerList,
                                           update_form=update_form)(request)


@login_required
def lbservice_delete(request):
    text = "Select which load balancer you wish to delete."
    header = "Load Balance Service - Delete"

    if request.session[SESSION_LB_TENANT] == None:
        return redirect('lbservice')

    def on_form_valid(form, service, roles):
        load_balancer = form.cleaned_data["load_balancer"]
        tenant = request.session[SESSION_LB_TENANT]
        host = utils.get_lbaas_host()
        try:
            atlas = utils.get_atlas_client()
            if atlas.delete_load_balancer(host, tenant, load_balancer):
                return redirect('install_checklist')
            else:
                return redirect('lbservice_info')
        except Exception, e:
            logger.error(e)
            request.session['LBAAS_LAST_ERROR'] = e
            return redirect('lbservice_info')
        finally:
            request.session[SESSION_LB_TENANT] = None
            request.session[SESSION_LB_LIST] = None

    def update_form(form, service, roles):
        host = utils.get_lbaas_host()
        tenant = request.session[SESSION_LB_TENANT]
        try:
            atlas = utils.get_atlas_client()
            raw_lb_list = atlas.get_load_balancers(host, tenant)
        except Exception, e:
            logger.error(e)
            request.session['LBAAS_LAST_ERROR'] = e
            return redirect('lbservice_info')
        lb_list = []
        for lb in raw_lb_list:
            if lb["status"] != 'DELETED':
                lb_list.append((lb["id"], lb["name"]))
        request.session[SESSION_LB_LIST] = lb_list
        form.add_load_balancers_into_form(lb_list)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=LoadBalancerDelete,
                                           update_form=update_form)(request)


@login_required
def lbservice_info(request):
    text = "There has been an error during the communication with the " + \
            "service: %s" % request.session['LBAAS_LAST_ERROR']
    header = "LBaaS Communication Failure"

    def on_form_valid(form, service, roles):
        return redirect('install_checklist')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=LBaaSInfoForm,
                                           update_form=update_form)(request)
