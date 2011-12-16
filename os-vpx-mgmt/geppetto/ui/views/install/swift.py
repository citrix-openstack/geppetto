from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.ui.forms.install import MultipleChoiceWorkerForm
from geppetto.ui.forms.install import SwiftStorageSizeForm
from geppetto.ui.forms.install import SwiftHashPathSuffixForm
from geppetto.ui.views import utils
from geppetto.core.models import Role
from geppetto.core.models import ConfigClassParameter

svc = utils.get_geppetto_web_service_client()


SWIFT_PROXY_SETUP_TASK_ID = "geppetto-swift-proxy-setup-task-id"
SWIFT_RING_SETUP_TASK_ID = "geppetto-swift-ring-setup-task-id"
SWIFT_DISK_SIZE = "geppetto-swift-disk-size"
SWIFT_HASH_PATH_SUFFIX = "geppetto-swift-hash-path-suffix"
SWIFT_STORAGE_NODE_HOSTNAMES = "geppetto-swift-storage-node-hostnames"


@login_required
def setup_swift_start(request):
    return redirect('setup_swift_hash_path_suffix')


@login_required
def setup_swift_hash_path_suffix(request):
    text = ("A suffix value should be set to some random string of text "
            "to be used as a salt when hashing to determine mappings "
            "in the swift ring. This should be the same on every node "
            "in the cluster.")
    header = "OpenStack Object Storage - Hash Path Suffix"

    def on_form_valid(form, service, roles):
        request.session[SWIFT_HASH_PATH_SUFFIX] = \
                                    form.cleaned_data["hash_path_suffix"]
        return redirect('setup_swift_storage_size')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=SwiftHashPathSuffixForm,
                                           update_form=update_form)(request)


@login_required
def setup_swift_storage_size(request):
    text = ("Two identically sized disks will be added to each of your "
            "Object Storage Workers. Please specify the size of those disks.")
    header = "OpenStack Object Storage - Disk Size"

    def on_form_valid(form, service, roles):
        size = form.cleaned_data["size"]
        request.session[SWIFT_DISK_SIZE] = size
        return redirect('setup_swift_storage')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=SwiftStorageSizeForm,
                                           update_form=update_form)(request)


@login_required
def setup_swift_storage(request):
    text = ("Please choose which workers should be OpenStack Object Storage "
            "Workers. You must choose a minimum of three nodes.")
    header = "OpenStack Object Storage - Object Storage Workers"

    def on_form_valid(form, service, roles):
        workers = form.clean_workers()
        request.session[SWIFT_STORAGE_NODE_HOSTNAMES] = workers
        return redirect('setup_swift_api')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.SWIFT_OBJECT])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                       on_form_valid=on_form_valid,
                                       django_form=MultipleChoiceWorkerForm,
                                       update_form=update_form,
                                       svc_proxy=svc)(request)


@login_required
def setup_swift_api(request):
    if (request.session[SWIFT_STORAGE_NODE_HOSTNAMES] == None) or \
                (request.session[SWIFT_DISK_SIZE] == None):
        return redirect('setup_swift_start')
    text = ("Please choose the node to become the Object Storage API. This "
            "server will give users, and the Imaging Service, access to "
            "items stored in the Object Storage system. You will be able "
            "to access this through the URL https://<hostname>/auth/v1.0")
    header = "OpenStack Object Storage - Object Storage API"

    def on_form_valid(form, service, roles):
        hash_suff = request.session[SWIFT_HASH_PATH_SUFFIX]
        service.Config.set(ConfigClassParameter.SWIFT_HASH_PATH_SUFFIX,
                           hash_suff)

        proxy = form.get_clean_worker()
        request.session[SWIFT_PROXY_SETUP_TASK_ID] = service.\
                                            ObjectStorage.add_apis([proxy], {})

        storage_nodes = request.session[SWIFT_STORAGE_NODE_HOSTNAMES]
        disk_size = request.session[SWIFT_DISK_SIZE]
        request.session[SWIFT_RING_SETUP_TASK_ID] = service.\
            ObjectStorage.add_workers(storage_nodes,
                                      {ConfigClassParameter.\
                                                SWIFT_DISK_SIZE_GB: disk_size})

        del request.session[SWIFT_STORAGE_NODE_HOSTNAMES]
        del request.session[SWIFT_DISK_SIZE]
        return redirect('setup_swift_progress')

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.SWIFT_PROXY])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form(node_details)

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


@login_required
def setup_swift_progress(request):
    return redirect('install_checklist')
