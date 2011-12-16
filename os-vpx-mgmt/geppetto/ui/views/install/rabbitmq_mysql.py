from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from geppetto.core.models import ConfigClassParameter, Role

from geppetto.ui.views import utils
from geppetto.ui.forms.install import ExternalRabbitMQ
from geppetto.ui.forms.install import ExternalMySQL

RABBIT_WORKER = "geppetto-rabbit-worker"
MYSQL_WORKER = "geppetto-mysql-worker"
EXTERNAL_WORKER = "EXTERNAL_WORKER"

MYSQL_TASK_ID = "geppetto-mysql-task-id"
RABBIT_TASK_ID = "geppetto-rabbit-task-id"

svc = utils.get_geppetto_web_service_client()


@login_required
def master_add_workers_for_supporting_roles(request):
    return redirect('setup_rabbitmq')


@login_required
def setup_rabbitmq(request):
    header = "Message Queue"
    text = "Please choose which OpenStack-VPX will run the RabbitMQ " + \
            "message queue service. Alternatively, you can use an existing" + \
            " external server."

    def on_form_valid(form, service, roles):
        worker = form.get_clean_worker()
        if worker == "external":
            return redirect('setup_rabbitmq_external')
        request.session[RABBIT_WORKER] = worker

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.RABBITMQ])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form_plus_external(node_details)

    return utils.generate_form_request_handler(header, text,
                                               on_form_valid=on_form_valid,
                                               update_form=update_form,
                                               finish_page="setup_mysql",
                                               svc_proxy=svc)(request)


@login_required
def setup_rabbitmq_external(request):
    header = "Message Queue - External"
    text = "Please specify the connection details for the RabbitMQ server."

    def on_form_valid(form, service, roles):
        service.Config.set(ConfigClassParameter.RABBIT_HOST,
                           form.cleaned_data["hostname"])
        service.Config.set(ConfigClassParameter.RABBIT_PORT,
                           form.cleaned_data["port"])
        service.Config.set(ConfigClassParameter.RABBIT_USER,
                           form.cleaned_data["username"])
        service.Config.set(ConfigClassParameter.RABBIT_PASS,
                           form.cleaned_data["password"])
        request.session[RABBIT_WORKER] = EXTERNAL_WORKER

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                               on_form_valid=on_form_valid,
                                               django_form=ExternalRabbitMQ,
                                               update_form=update_form,
                                               finish_page="setup_mysql",
                                               svc_proxy=svc)(request)


@login_required
def setup_mysql(request):
    header = "Database"
    text = "Please choose which OpenStack-VPX will run the MySQL database" + \
            ". Alternatively, you can use an existing external server."

    def update_form(form, service, roles):
        node_fqdns = service.Node.exclude_by_roles([Role.MYSQL])
        node_details = service.Node.get_details(node_fqdns)
        form.add_workers_into_form_plus_external(node_details)

    def on_form_valid(form, service, roles):
        worker = form.get_clean_worker()
        if worker == "external":
            return redirect('setup_mysql_external')
        request.session[MYSQL_WORKER] = worker

    return utils.generate_form_request_handler(header, text,
                                               on_form_valid=on_form_valid,
                                               update_form=update_form,
                                        finish_page="progress_mysql_rabbitmq",
                                        svc_proxy=svc)(request)


@login_required
def setup_mysql_external(request):
    header = "Database - External"
    text = "Please specify the connection details for the MySQL server."

    def on_form_valid(form, service, roles):
        service.Config.set(ConfigClassParameter.MYSQL_TYPE, "external")
        service.Config.set(ConfigClassParameter.MYSQL_HOST,
                           form.cleaned_data["hostname"])
        service.Config.set(ConfigClassParameter.MYSQL_USER,
                           form.cleaned_data["username"])
        service.Config.set(ConfigClassParameter.MYSQL_PASS,
                           form.cleaned_data["password"])
        request.session[MYSQL_WORKER] = EXTERNAL_WORKER

    def update_form(form, service, roles):
        pass

    return utils.generate_form_request_handler(header, text,
                                               on_form_valid=on_form_valid,
                                               django_form=ExternalMySQL,
                                               update_form=update_form,
                               finish_page="progress_mysql_rabbitmq",
                               svc_proxy=svc)(request)


def progress(request):
    if (request.session[RABBIT_WORKER] == None) or \
                        (request.session[MYSQL_WORKER] == None):
        return redirect('install_checklist')

    mysql_task_id = svc.Compute.add_database(request.session[MYSQL_WORKER],
                               {ConfigClassParameter.MYSQL_PASS: "citrix"})
    request.session[MYSQL_TASK_ID] = mysql_task_id
    rabbit_task_id = svc.\
                    Compute.add_message_queue(request.session[RABBIT_WORKER])
    request.session[RABBIT_TASK_ID] = rabbit_task_id

    return redirect('install_checklist')
