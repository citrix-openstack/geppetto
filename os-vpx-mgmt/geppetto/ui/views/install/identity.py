from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.ui.views import utils
from geppetto.core.models import Role

IDENTITY_TASK_ID = "geppetto-identity-task-id"

svc = utils.get_geppetto_web_service_client()


@login_required
def setup_identity(request):
    header = "OpenStack Identity"
    text = "Please choose which OpenStack-VPX will run the OpenStack " + \
           "Identity service."

    def on_form_valid(form, service, roles):
        worker = form.get_clean_worker()
        geppetto_service = utils.get_geppetto_web_service_client()
        identity_task_id = geppetto_service.Identity.add_auth(worker, {})
        request.session[IDENTITY_TASK_ID] = identity_task_id
        return redirect('install_checklist')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.KEYSTONE_AUTH])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)
