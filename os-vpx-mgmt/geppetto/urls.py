from django.conf.urls.defaults import *
from django.contrib import admin
import django.contrib.admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^openstack/', include('geppetto.core.urls')),
    (r'^', include('geppetto.ui.urls'))
)

import djcelery.urls
urlpatterns += patterns('',
    (r'^celery/', include(djcelery.urls)),)

if settings.ADD_STATIC_CONTENT_URLS:
    # TODO - we should do this with a proper web server...
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': (django.contrib.admin.__path__[0] + '/media'),
             'show_indexes': True}),
        (r'^(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.GEPPETTO_MEDIA_DIR,
             'show_indexes': True}),
        )
