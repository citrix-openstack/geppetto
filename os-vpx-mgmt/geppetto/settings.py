# Django settings for django_tutorial project.
import os
import logging

DEBUG = False
TEMPLATE_DEBUG = DEBUG
ADD_STATIC_CONTENT_URLS = True
GEPPETTO_MEDIA_DIR = \
    os.path.normpath(os.path.join(os.path.dirname(__file__),
                                  '../geppetto-media')).replace('\\', '/')

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'sqlite3.db~',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {'timeout': 20, }
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1d4hj2v&*+qf6nt045w+0qss)vg%0j$_e-7^59de5)9=_%1!is'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'geppetto.urls'

TEMPLATE_DIRS = (
    #"/home/johngar/workspace/openstack/django_tutorial/templates"
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\', '/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'geppetto.core',
    'geppetto.ui',
    'django.contrib.admin',
    'djcelery',
    'djkombu',
    'geppetto.tasks',
    'south',
)

# timeout after 15mins when waiting for node to become stable
GEPPETTO_TASK_MAX_RETRIES = 15
GEPPETTO_TASK_RETRY_DELAY = 60
GEPPETTO_LOG_LEVEL = logging.DEBUG

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Celery setup
import djcelery
djcelery.setup_loader()

BROKER_TRANSPORT = "amqplib"
CELERYD_CONCURRENCY = 2
CELERYD_LOG_LEVEL = "DEBUG"

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"

CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True
