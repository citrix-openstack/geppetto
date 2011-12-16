from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext, TemplateDoesNotExist

import logging

log = logging.getLogger(__name__)


@login_required
def root(request):
    # TODO - decide if we need to do the first time, and which bit
    return redirect('install_checklist')


@login_required
def common(request, page_name):
    try:
        return render_to_response('ui/%s.html' % page_name, locals(),
                              context_instance=RequestContext(request))
    except TemplateDoesNotExist:
        raise Http404


@login_required
def unassigned_workers_list(request):
    return render_to_response('ui/unassigned_workers_list.html', locals(),
                              context_instance=RequestContext(request))
