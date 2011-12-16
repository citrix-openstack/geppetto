import logging

from django import shortcuts
from django.contrib.auth import decorators

from geppetto.core.models.roledependencies import DEFAULT_ROLES
from geppetto.ui.forms import upgrade
from geppetto.ui.views import utils

logger = logging.getLogger('geppetto.ui.views')
svc = utils.get_geppetto_web_service_client()

SESSION_VAR_OS_WORKER_ROLES = 'OS_WORKER_ROLES'
SESSION_VAR_OS_WORKER_LABEL = 'OS_WORKER_LABEL'
SESSION_VAR_OLD_VPX = 'OLD_VPX'
SESSION_VAR_NEW_VPX = 'NEW_VPX'


@decorators.login_required
def select_role(request):
    text = ("Please, select a role in order to choose which worker "
            "you would like to upgrade.")
    header = "Upgrade VPX - Select OpenStack Worker"

    def on_form_valid(form, service, roles):
            request.session[SESSION_VAR_OS_WORKER_ROLES] = \
                        form.cleaned_data['openstack_worker']
            request.session[SESSION_VAR_OS_WORKER_LABEL] = \
                        form.get_openstack_worker_label(form.\
                             cleaned_data['openstack_worker'])
            return shortcuts.redirect('select_vpx')

    def update_form(form, service, roles):
        form.load_worker_roles(service.Role.get_compositions())

    return utils.generate_form_request_handler(header, text,
                                          on_form_valid=on_form_valid,
                                          django_form=upgrade.SelectWizardForm,
                                          update_form=update_form,
                                          svc_proxy=svc)(request)


@decorators.login_required
def select_vpx(request):
    text = ("Select two VPXs: the first one is the node whose roles "
            "and configs need to be rolled over a brand new VPX.")
    header = "Upgrade VPX - Select VPX Node"

    def on_form_valid(form, service, roles):
            o_vpx = form.cleaned_data['old_vpx']
            n_vpx = form.cleaned_data['new_vpx']
            request.session[SESSION_VAR_OLD_VPX] = o_vpx
            request.session[SESSION_VAR_NEW_VPX] = n_vpx
            return shortcuts.redirect('confirm_vpx')

    def update_form(form, service, roles):
        roles = request.session[SESSION_VAR_OS_WORKER_ROLES]
        o_vpxs = service.Node.get_by_roles(eval(roles))

        n_vpxs = _get_new_nodes()
        form.load_nodes(service.Node.get_details(o_vpxs), n_vpxs)

    return utils.generate_form_request_handler(header, text,
                                       on_form_valid=on_form_valid,
                                       django_form=upgrade.MigrationWizardForm,
                                       update_form=update_form,
                                       svc_proxy=svc)(request)


def _get_new_nodes():
    all_nodes = svc.Node.get_all()
    all_node_details = svc.Node.get_details(all_nodes)
    new_nodes = {}
    for node_fqdn in all_node_details.keys():
        node_details = all_node_details[node_fqdn]
        if len(node_details['roles']) == len(DEFAULT_ROLES):
            new_nodes[node_fqdn] = node_details
    return new_nodes


@decorators.login_required
def confirm_vpx(request):
    text = ("You are about to migrate roles and configuration from "
            "%s to %s. Please note, all roles will be migrated, and "
            "%s will be no longer in use. Click Next to continue."
            % (request.session[SESSION_VAR_OLD_VPX],
               request.session[SESSION_VAR_NEW_VPX],
               request.session[SESSION_VAR_OLD_VPX]))
    header = "Upgrade VPX - Confirmation"

    def on_form_valid(form, service, roles):
        return shortcuts.redirect('migrate_vpx')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                       on_form_valid=on_form_valid,
                                       django_form=upgrade.WarningWizardForm,
                                       update_form=update_form)(request)


@decorators.login_required
def migrate_vpx(request):
    svc.Node.copy(request.session[SESSION_VAR_OLD_VPX],
                  request.session[SESSION_VAR_NEW_VPX])

    del request.session[SESSION_VAR_OS_WORKER_ROLES]
    del request.session[SESSION_VAR_OS_WORKER_LABEL]
    del request.session[SESSION_VAR_OLD_VPX]
    del request.session[SESSION_VAR_NEW_VPX]
    return shortcuts.redirect('install_checklist')
