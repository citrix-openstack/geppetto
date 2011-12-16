from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.core.models import Role, ConfigClassParameter
from geppetto.ui.views import utils
from geppetto.ui.forms.install import ChooseBlockStorage, DefineISCSIDiskSize

SESSION_VAR_BLOCK_WORKER = "GeppettoBlockWorker"
BLOCK_STORAGE_TASK_ID = "geppetto-block-storage-task-id"

svc = utils.get_geppetto_web_service_client()


@login_required
def setup_worker(request):
    text = "Please select which OpenStack VPX you want to be the " + \
            "OpenStack Volume Worker, along with what type of block " + \
            "storage you want."
    header = "OpenStack Volume Worker"

    def on_form_valid(form, service, roles):
            storage_type = form.cleaned_data["storage_type"]
            worker = form.get_clean_worker()
            config = {}
            config["TYPE"] = storage_type
            request.session["config"] = config
            if storage_type == "iscsi":
                request.session[SESSION_VAR_BLOCK_WORKER] = worker
                return redirect('setup_block_storage_iscsi')
            elif storage_type == "xenserver_sm":
                request.session[SESSION_VAR_BLOCK_WORKER] = worker
                return redirect('setup_block_storage_sm')
            else:
                raise Exception("Invalid Storage Type")

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.NOVA_VOLUME])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=ChooseBlockStorage,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


@login_required
def setup_iscsi(request):
    text = "Please specify the disk size for the given worker."
    header = "OpenStack Volume Worker - iSCSI Setup"

    def on_form_valid(form, service, roles):
        disk_size = form.cleaned_data["disk_size"]
        config = request.session["config"]
        config[ConfigClassParameter.VOLUME_DISK_SIZE_GB] = disk_size
        request.session["config"] = config
        return redirect('setup_block_complete')

    def update_form(form, service, roles):
        form.update_worker(request.session[SESSION_VAR_BLOCK_WORKER])

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=DefineISCSIDiskSize,
                                           update_form=update_form)(request)


@login_required
def setup_sm(request):
    return redirect('setup_block_complete')


#add setup_volume_complete to urls file
@login_required
def setup_block_complete(request):
    worker = request.session[SESSION_VAR_BLOCK_WORKER]
    config = request.session["config"]
    request.session[BLOCK_STORAGE_TASK_ID] = \
                svc.BlockStorage.add_workers([worker], config)
    del request.session[SESSION_VAR_BLOCK_WORKER]
    return redirect('install_checklist')
    # TODO -- show progress??
