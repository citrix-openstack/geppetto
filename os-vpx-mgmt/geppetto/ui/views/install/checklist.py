from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from geppetto.geppettolib import puppet

from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Role
from geppetto.core.views import service_proxy

from geppetto.ui.views.install import swift
from geppetto.ui.views.install import rabbitmq_mysql
from geppetto.ui.views.install import identity


class ProgressState():
    not_started = "not_started"
    pending = "pending"
    success = "success"
    failure = "failure"
    none = "none"


@login_required
def install_checklist(request):
    bl = InstallChecklistBL()

    hypervisor_complete = bl.is_hypervisor_complete()
    identity_complete = bl.is_identity_complete()
    rabbit_mysql_complete = bl.is_rabbit_mysql_complete()
    imaging_complete = bl.is_imaging_complete()
    compute_management_complete = bl.is_compute_management_complete()
    compute_controller_complete = bl.is_compute_controller_complete()
    nova_complete = rabbit_mysql_complete and compute_management_complete
    swift_complete = bl.is_swift_complete()
    block_storage_complete = bl.is_block_storage_complete()
    compute_network_complete = bl.is_compute_network_complete()
    compute_complete = compute_controller_complete and \
            block_storage_complete and compute_management_complete and \
            compute_network_complete
    dashboard_url = bl.get_service_url(Role.OPENSTACK_DASHBOARD, \
                                       'http', '9999')
    lbservice_url = bl.get_service_url(Role.LBSERVICE, 'http', '8888')

    hypervisor_status = _get_status_from_legacy_flag(hypervisor_complete)
    imaging_status = _get_status_from_legacy_flag(imaging_complete)
    compute_status = _get_status_from_legacy_flag(compute_complete)

    identity_status = _get_status_from_task(bl.svc,
                                            request.session,
                                            [identity.IDENTITY_TASK_ID],
                                            identity_complete)
    swift_status = _get_status_from_task(bl.svc,
                                         request.session,
                                         [swift.SWIFT_PROXY_SETUP_TASK_ID,
                                          swift.SWIFT_RING_SETUP_TASK_ID],
                                          swift_complete)
    rabbit_mysql_status = _get_status_from_task(bl.svc,
                                                request.session,
                                                [rabbitmq_mysql.RABBIT_TASK_ID,
                                                 rabbitmq_mysql.MYSQL_TASK_ID],
                                                 rabbit_mysql_complete)

    return render_to_response('ui/install_checklist.html', locals(),
                              context_instance=RequestContext(request))


def _get_status_from_legacy_flag(is_complete):
    if is_complete:
        return ProgressState.success
    else:
        return ProgressState.not_started


def _get_status_from_task(service, session, task_session_keys, legacy_flag):
    overall_state = ProgressState.pending
    for task_session_key in task_session_keys:
        try:
            task_id = session[task_session_key]
        except KeyError:
            # TODO - we need to replace session with task registry
            return  _get_status_from_legacy_flag(legacy_flag)

        task_state = service.Task.get_status(task_id)

        if task_state == "FAILURE":
            overall_state = ProgressState.failure
            break

        if task_state == "SUCCESS":
            overall_state = ProgressState.success
            del session[task_session_key]

        elif task_state != "PENDING" and task_state != "RETRY":
            raise Exception("Unknown task state: %s" % task_state)

    return overall_state


class InstallChecklistBL():

    def __init__(self):
        try:
            master_fqdn = puppet.PuppetNode().get_puppet_option('server')
        except:
            master_fqdn = 'localhost'
        self.svc = service_proxy.create_proxy(master_fqdn, 8080,
                                              service_proxy.Proxy.Geppetto,
                                              'v1')

    def is_hypervisor_complete(self):
        return self.svc.Config.get(ConfigClassParameter.HAPI_PASS) != " "

    def is_identity_complete(self):
        return self.svc.Role.has_node(Role.KEYSTONE_AUTH)

    def is_rabbit_mysql_complete(self):
        return (self.svc.Role.has_node(Role.RABBITMQ) and \
                    self.svc.Role.has_node(Role.MYSQL)) or \
                    self.svc.Config.get(ConfigClassParameter.\
                                                MYSQL_TYPE) == "external"

    def is_imaging_complete(self):
        return self.svc.Role.has_node(Role.GLANCE_API) and \
                self.svc.Role.has_node(Role.GLANCE_REGISTRY)

    def is_compute_management_complete(self):
        return self.svc.Role.has_node(Role.NOVA_API) and \
                self.svc.Role.has_node(Role.NOVA_SCHEDULER)

    def is_compute_network_complete(self):
        #This will grey out the link for the network worker either if
        #the worker has been configured or if a compute worker has been
        #configure in HA mode. Makes sense to me (salvatore).
        return self.svc.Role.has_node(Role.NOVA_NETWORK)

    def is_compute_controller_complete(self):
        return self.svc.Role.has_node(Role.NOVA_COMPUTE)

    def is_swift_complete(self):
        return self.svc.Role.has_node(Role.SWIFT_PROXY) and \
                self.svc.Role.has_node(Role.SWIFT_OBJECT)

    def is_block_storage_complete(self):
        return self.svc.Role.has_node(Role.NOVA_VOLUME)

    def get_service_url(self, role_name, protocol, port):
        url = ''
        node_fqdns = self.svc.Node.get_by_role(role_name)
        if len(node_fqdns) > 0:
            url = '%s://%s:%s' % (protocol, node_fqdns[0], port)
        return url
