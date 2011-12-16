from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.ui.views import utils
from geppetto.core.models import Role

COMPUTE_WORKER_TASK_ID = "geppetto-compute-worker-task_id"


@login_required
def add_compute_node(request):
    text = "You need an OpenStack Compute Worker running on every " \
            "Hypervisor on which you wish to run VM instances. There "  \
            "must be only one per physical machine."
    header = "OpenStack Compute Worker"
    svc = utils.get_geppetto_web_service_client()

    def on_form_valid(form, service, roles):
        worker = form.get_clean_worker()
        copute_worker_task_id = service.Compute.add_workers([worker], {})
        request.session[COMPUTE_WORKER_TASK_ID] = copute_worker_task_id
        return redirect('install_checklist')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.NOVA_COMPUTE])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)
