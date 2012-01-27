import eventlet
import getpass
import logging
import os

from eventlet import wsgi
from django.core.handlers import wsgi as django_wsgi
from django.conf import settings


LOG_LEVEL = logging.DEBUG


os.environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'
os.environ['PYTHON_EGG_CACHE'] = '/tmp/%s/PYTHON_EGG_CACHE' % getpass.getuser()
application = django_wsgi.WSGIHandler()


class WritableLogger(object):
    """A thin wrapper that responds to `write` and logs."""

    def __init__(self, logger, level=logging.DEBUG):
        self.logger = logger
        self.level = level

    def write(self, msg):
        self.logger.log(self.level, msg)


class Server(object):
    """Server class to manage multiple WSGI sockets and applications."""

    def __init__(self, threads=1000):
        self.pool = eventlet.GreenPool(threads)

    def start(self, application, port, host, backlog=128):
        """Run a WSGI server with the given application."""
        logging.info(("Starting Dashboard on %(host)s:%(port)s") % locals())
        socket = eventlet.listen((host, port), backlog=backlog)
        self.pool.spawn_n(self._run, application, socket)

    def wait(self):
        """Wait until all servers have completed running."""
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass

    def _run(self, application, socket):
        """Start a WSGI server in a new green thread."""
        logger = logging.getLogger('eventlet.wsgi')
        wsgi.server(socket, application, custom_pool=self.pool,
                             log=WritableLogger(logger))


def run_eventlet_server(port, host='0.0.0.0'):
    _configure_logging()
    eventlet.monkey_patch()
    server = Server()
    server.start(application, port, host)
    server.wait()


def _configure_logging():
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    hdlr = logging.handlers.SysLogHandler('/dev/log', \
           facility=logging.handlers.SysLogHandler.LOG_USER)
    formatter = \
        logging.Formatter('openstack-dashboard: %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(hdlr)
