import logging
import os
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.files import uploadhandler
from django.core.files import uploadedfile
from django.core.files import temp as tempfile
from django.template import RequestContext
from django.shortcuts import render_to_response
##FIXME  Remove the above two imports when setup_and_upload is shifted to new
##         api

from geppetto.core.models import ConfigClassParameter
from geppetto.core.models import Role
from geppetto.geppettolib import network

from geppetto.geppettolib.utils import execute

from geppetto.ui.views import utils
from geppetto.ui.forms.images import ImportPrepForm
from geppetto.ui.forms.images import UploadImageForm
from geppetto.ui.forms.images import SetupImageContainerForm


logger = logging.getLogger('geppetto.ui.views')
svc = utils.get_geppetto_web_service_client()


IMAGES_CONTAINER_PATH_PREFIX = '/var/lib/geppetto/images'


@login_required
def setup_image_container(request):
    text = "Please specify the size of the disk \
                              that is going to contain your images."
    header = "Community Images Setup"
    if os.path.exists(IMAGES_CONTAINER_PATH_PREFIX):
            return redirect('images_upload')

    def on_form_valid(form, service, roles):
        # Setup image container
        _create_container(service, form.cleaned_data['disk_size'])
        _wait_containter(180, 2)
        return redirect('images_upload')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=SetupImageContainerForm,
                                           update_form=update_form,
                                           svc_proxy=svc)(request)


##FIXME move setup_and_upload to use utils.generate_form_request_handler
@login_required
def select_and_upload(request):
    settings.FILE_UPLOAD_TEMP_DIR = IMAGES_CONTAINER_PATH_PREFIX
    settings.FILE_UPLOAD_HANDLERS = ("geppetto.ui.views.install." + \
                         "images_upload.StickyTemporaryFileUploadHandler",)
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            # upload process
            request.session['label'] = form.cleaned_data['label']
            request.session['hypervisor'] = form.cleaned_data['hypervisor']
            if(request.session['hypervisor'] == 'esx'):
                request.session['ostype'] = form.cleaned_data['ostype']
            machine = request.FILES['machine']
            request.session['machine'] = machine.temporary_file_path()
            kernel = None
            if 'kernel' in request.FILES:
                kernel = request.FILES['kernel']
                request.session['kernel'] = kernel.temporary_file_path()
            ramdisk = None
            if 'ramdisk' in request.FILES:
                ramdisk = request.FILES['ramdisk']
                request.session['ramdisk'] = ramdisk.temporary_file_path()
            return redirect('images_register')
    else:
        form = UploadImageForm()
    return render_to_response('ui/install_step.html',
                              {'form': form,
                               'require_multipart': True,
                     'text': "Please choose a label and select the Machine" + \
                     ", Kernel, Ramdisk and Hypervisor you would like to " + \
                     "upload. Kernel, Ramdisk are optional. NOTE: If you " + \
                     "choose Hypervisor as ESX(i) ,you must specify the " + \
                     "ostype as well. ",
                                'header': "Community Images Upload"},
                                context_instance=RequestContext(request))


@login_required
def nova_manage_register(request):
    text = "The upload process has succeded. \
                               Please, click the next button to start the \
                               registration process. This will import the \
                               images into the registry, and may take a while \
                               depending on your storage back-end (i.e. \
                               Swift, file system etc)."
    header = "Community Images Registration"

    def on_form_valid(form, service, roles):
        geppetto_service = utils.get_geppetto_web_service_client()
        auth_token = geppetto_service.Config.get(\
                              ConfigClassParameter.KEYSTONE_SUPERUSER_TOKEN)
        requested_ostype = None
        if ('kernel' in request.session) and ('ramdisk' in request.session):
            _nova_manage_register(auth_token,
                                  request.session['label'],
                                  request.session['machine'],
                                  request.session['kernel'],
                                  request.session['ramdisk'],
                                  request.session['hypervisor'])

        else:
            if request.session['hypervisor'] == 'esx':
                requested_ostype = request.session['ostype']
            _nova_manage_register(auth_token,
                                  request.session['label'],
                                  request.session['machine'], None, None,
                                  request.session['hypervisor'],
                                  requested_ostype)
        return redirect('install_checklist')

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                           on_form_valid=on_form_valid,
                                           django_form=ImportPrepForm,
                                           update_form=update_form)(request)


def _create_container(service, size):
    try:
        # Setup Geppetto DB
        if not service.Role.has_node(Role.IMG_CONTAINER):
            # Currently we force the image container to run on the master
            master_node = network.get_hostname()
            service.Imaging.add_container(master_node,
                                          {ConfigClassParameter.\
                                           IMG_CONTAINER_SIZE: size})
    except Exception, e:
        logger.error(e)


def _wait_containter(timeout, delay):
    for _ in xrange(timeout):
        if os.path.exists(IMAGES_CONTAINER_PATH_PREFIX + "/lost+found"):
            logger.debug("Found images/lost+found directory")
            break
        logger.debug("Not yet found images/lost+found directory")
        time.sleep(delay)


def _nova_manage_register(auth_token, label, machine, kernel=None, \
                      ramdisk=None, hypervisor='xenserver', ostype=None, \
                    adaptertype='lsiLogic'):
    to_log = '&> /var/log/geppetto/nova-manage-register-%s' % time.time()
    # Choose image type
    if kernel is None and ramdisk is None:
        nova_manage_cmd = '/usr/local/bin/nova-manage image image_register'
        nova_manage_fmt = '%(nova_manage_cmd)s %(machine)s ' + \
            '--owner=root ' + \
            '--name="%(label)s" --auth_token=%(auth_token)s %(to_log)s'
    else:
        nova_manage_cmd = '/usr/local/bin/nova-manage image all_register'
        nova_manage_fmt = '%(nova_manage_cmd)s %(machine)s %(kernel)s ' + \
            '%(ramdisk)s --owner=root ' + \
            '--name="%(label)s" --auth_token=%(auth_token)s %(to_log)s'
    # Register with registry
    try:
        execute(nova_manage_fmt % locals())
        logger.debug('nova-manage register: done!')
    except Exception, e:
        logger.error('Nova manage: failure')
        logger.error(e)
        raise Exception("Failed to register image")
    finally:
        _delete_fileset([machine, kernel, ramdisk])

def _delete_fileset(files):
    for file in files:
        try:
            logger.debug('Removing file: %s' % file)
            if file is not None:
                os.remove(file)
                logger.debug('File %s: deleted' % file)
        except (IOError, OSError), e:
            logger.debug('File %s: unable to delete')
            logger.error(e)


# This is a hack for OS-344
class StickyTemporaryFileUploadHandler(\
                                    uploadhandler.TemporaryFileUploadHandler):
    def __init__(self, *args, **kwargs):
        super(StickyTemporaryFileUploadHandler, self).__init__(*args, **kwargs)

    def new_file(self, file_name, *args, **kwargs):
        try:
            super(StickyTemporaryFileUploadHandler, \
                        self).new_file(file_name, *args, **kwargs)
            self.file = StickyTemporaryUploadedFile(self.file_name, \
                                        self.content_type, 0, self.charset)
        except OSError, e:
            logger.error(e)
            raise


class StickyTemporaryUploadedFile(uploadedfile.UploadedFile):
    def __init__(self, name, content_type, size, charset):
        # AM: since we are using the file across the session
        # and I cannot store the object in the session I need
        # to keep the file and delete it manually.
        path = settings.FILE_UPLOAD_TEMP_DIR
        file = tempfile.NamedTemporaryFile(suffix='.upload',
                                           dir=path,
                                           delete=False)
        super(StickyTemporaryUploadedFile, self).__init__(file, name, \
                                                  content_type, size, charset)

    def temporary_file_path(self):
        return self.file.name

    def close(self):
        try:
            return self.file.close()
        except OSError, e:
            if e.errno != 2:
                raise
