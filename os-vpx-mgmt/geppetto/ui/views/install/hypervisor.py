from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.hapi import config_util
from geppetto.core.models import ConfigClassParameter
from geppetto.ui.forms.install import PasswordForm
from geppetto.ui.views import utils

svc = utils.get_geppetto_web_service_client()


@login_required
def setup_password(request):
    hypervisor_description = config_util.get_running_hypervisor_description()
    hypervisor_dependent_text = "The OpenStack VPX requires access to the" + \
                    " hypervisor's host. Please specify the root password" + \
                    " for the %(hypervisor_description)s hosts." % locals()
    hypervisor_dependent_header = "Hypervisor Integration - " + \
                                "%(hypervisor_description)s" % locals()
    header = hypervisor_dependent_header
    text = hypervisor_dependent_text

    def on_form_valid(form, service, roles):
        service.Config.set(ConfigClassParameter.HAPI_PASS,
                           form.cleaned_data["password"])
        return redirect('install_checklist')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=PasswordForm,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)
