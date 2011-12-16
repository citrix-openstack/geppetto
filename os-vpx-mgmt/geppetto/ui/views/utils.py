from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from geppetto.geppettolib import puppet
from geppetto.core.models import Role
from geppetto.core.views import service_proxy
from geppetto.geppettolib.ec2_client import EC2Client

from geppetto.core.views.atlas_service import Service as AtlasService
from geppetto.ui.forms.install import ChooseWorkerForm


def get_geppetto_web_service_client():
    try:
        master_fqdn = puppet.PuppetNode().get_puppet_option('server')
    except:
        master_fqdn = 'localhost'
    return service_proxy.create_proxy(master_fqdn, 8080,
                                      service_proxy.Proxy.Geppetto, 'v1')


def get_ec2_client():
    client = EC2Client(get_nova_api_host())
    return client


def get_nova_api_host():
    return get_geppetto_web_service_client().Node.get_by_role(Role.NOVA_API)


def get_lbaas_host():
    return get_geppetto_web_service_client().Node.get_by_role(Role.LBSERVICE)


def get_atlas_client():
    return AtlasService()


def add_workers_to_choose_worker_form(form, service, roles):
    node_fqdns = service.Node.exclude_by_roles(roles)
    node_details = service.Node.get_details(node_fqdns)
    form.add_workers_into_form(node_details)


def add_worker_to_roles(form, service, roles):
    raise NotImplementedError()


def generate_form_request_handler(header, text,
                              on_form_valid=add_worker_to_roles,
                              roles=[],
                              django_form=ChooseWorkerForm,
                              update_form=add_workers_to_choose_worker_form,
                              finish_page="install_checklist",
                              svc_proxy=get_geppetto_web_service_client()):
    """
    This function returns a function that will process a request
    and either show a form, or process the post from a form

    The arguments are:
        header - text for the top of the form
        text - text for the body of the form
        on_form_valid - given (form, service, roles)is called on a post if
        the form is valid
        roles - list of roles the node is being added into, gets passed to all
        the methods, only supply if needed
        django_form - the form that should be displayed
        update_from - given (form, service, roles) should update the form like
        add list of workers
        finish_page - redirects to this page if form that is posted to is valid
        and on_forms_valid doesn't return anything
    """

    @login_required
    def handle_form(request):
        service = svc_proxy
        if (request.method == 'POST'):
            form = django_form(request.POST)
            update_form(form=form, service=service, roles=roles)
            if form.is_valid():
                on_form_valid_result = on_form_valid(form=form, \
                                                service=service, roles=roles)
                if on_form_valid_result != None:
                    return on_form_valid_result
                else:
                    return redirect(finish_page)
        else:
            form = django_form()
            update_form(form=form, service=service, roles=roles)
        return render_to_response('ui/install_step.html',
                              {'form': form, 'text': text, 'header': header},
                                  context_instance=RequestContext(request))
    return handle_form
