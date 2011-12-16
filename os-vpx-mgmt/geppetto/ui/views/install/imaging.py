"""Setting up Glance"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.ui.views import utils
from geppetto.ui.forms.install import SetupGlance
from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Role

IMAGING_TASK_ID = "geppetto-imaging-task-id"
svc = utils.get_geppetto_web_service_client()


@login_required
def setup_imaging(request):
    header = "OpenStack Imaging"
    text = "Please choose the node for the OpenStack Imaging API and" + \
                " OpenStack Imaging Registry."

    def on_form_valid(form, service, roles):
        glance_store = form.cleaned_data["default_storage"]
        extra_data = form.cleaned_data["extra_data"]
        config = {}
        config[ConfigClassParameter.GLANCE_STORE] = glance_store
        if glance_store == "file":
            config[ConfigClassParameter.GLANCE_FILE_STORE_SIZE_GB] = extra_data
        else:
            config[ConfigClassParameter.GLANCE_SWIFT_ADDRESS] = extra_data
        worker = form.get_clean_worker()
        config[ConfigClassParameter.GLANCE_HOSTNAME] = worker
        imaging_task_id = service.Imaging.add_registry(worker, config)
        request.session[IMAGING_TASK_ID] = imaging_task_id
        return redirect('install_checklist')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.GLANCE_API])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)
        nodes = service.Node.get_by_role(Role.SWIFT_PROXY)
        swift_proxy = nodes[0] if len(nodes) == 1 else ''
        form.update_swift_api_hostname(swift_proxy)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=SetupGlance,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)
