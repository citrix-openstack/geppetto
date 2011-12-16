from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext

from geppetto.geppettolib.utils import execute
from geppetto.ui.forms.config import CreateNetwork
from geppetto.ui.forms.config import CreateFloatingIPs

import logging
import time

logger = logging.getLogger('geppetto.ui.views.config.nova.network')


@login_required
def network_create(request):
    if request.method == 'POST':
        form = CreateNetwork(request.POST)
        if form.is_valid():
            _execute_network_create(form.cleaned_data['command_line'])
            return redirect('install_checklist')
    else:
        form = CreateNetwork()
    text = ("You can create networks that will be added into the Nova "
            "database and used to hand out IP address to instances. "
            "You can specify the commandline sent to nova-manage network "
            "create using the line below. Click submit to accept the "
            "defaults.")
    return render_to_response('ui/install_step.html',
                             {'form': form,
                              'text': text,
                              'header': "Create Network"},
                              context_instance=RequestContext(request))


def _execute_network_create(arg):
    logger.debug("nova-manage create network arguments:%s", arg)
    log_file_name = \
        "/var/log/geppetto/nova-manage-network-create-%s" % time.time()
    execute("echo calling nova-manage with "
            "the args: network create %s >> %s" % (arg, log_file_name))
    execute("/usr/local/bin/nova-manage "
            "network create %s >> %s 2>&1" % (arg, log_file_name))


@login_required
def floating_create(request):
    if request.method == 'POST':
        form = CreateFloatingIPs(request.POST)
        if form.is_valid():
            _execute_floating_ips_create(form.cleaned_data['command_line'])
            return redirect('install_checklist')
    else:
        form = CreateFloatingIPs()
    text = ("You can floating IPs by specifying floating IP range. "
            "The block of floating IPs will be available for allocation "
            "to tenants in cloud. You can specify the commandline sent to "
            "nova-manage floating create using the line below.")
    return render_to_response('ui/install_step.html',
                             {'form': form,
                              'text': text,
                              'header': "Create FloatingIPs"},
                              context_instance=RequestContext(request))


def _execute_floating_ips_create(arg):
    logger.debug("nova-manage floating create arguments:%s", arg)
    log_file_name = \
        "/var/log/geppetto/nova-manage-floating-create-%s" % time.time()
    execute("echo calling nova-manage "
            "with the args: floating create %s >> %s" % (arg, log_file_name))
    execute("/usr/local/bin/nova-manage "
            "floating create %s >> %s 2>&1" % (arg, log_file_name))
