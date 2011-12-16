from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.ui.views import utils
from geppetto.ui.forms.install import ScaleOutChooseRole
from geppetto.core.models import Role

SESSION_VAR_ROLE = "GeppettoChosenRole"
SESSION_SCALEOUT_TASK_ID = "geppetto-scaleout-task-id"

svc = utils.get_geppetto_web_service_client()


@login_required
def scaleout_choose_role(request):
    text = "Please specify for which role you wish to add extra capacity."
    header = "Scale out Cloud - Choose Role"

    def on_form_valid(form, service, roles):
        type_of_node = form.cleaned_data["type_of_node"]
        if type_of_node == "nova-compute":
            request.session[SESSION_VAR_ROLE] = Role.NOVA_COMPUTE
        elif type_of_node == "nova-api":
            request.session[SESSION_VAR_ROLE] = Role.NOVA_API
        return redirect('scaleout_choose_worker')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=ScaleOutChooseRole,
                                           update_form=update_form)(request)


@login_required
def scaleout_choose_worker(request):
    chosen_role = request.session[SESSION_VAR_ROLE]
    if chosen_role == None:
        return redirect('scaleout_choose_role')
    text = "Please specify which worker you wish to use to add the " + \
            "extra capacity:"
    header = "Scale out Cloud - Choose Worker"

    def on_form_valid(form, service, roles):
        chosen_role = request.session[SESSION_VAR_ROLE]
        worker = form.get_clean_worker()
        if chosen_role == Role.NOVA_COMPUTE:
            scaleout_task_id = svc.Compute.add_workers([worker], {})
            request.session[SESSION_SCALEOUT_TASK_ID] = scaleout_task_id
        elif chosen_role == Role.NOVA_API:
            scaleout_task_id = svc.Compute.add_apis([worker], {})
            request.session[SESSION_SCALEOUT_TASK_ID] = scaleout_task_id

        return redirect('install_checklist')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([chosen_role])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)
