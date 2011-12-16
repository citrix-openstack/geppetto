from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('django.contrib.auth.views',
    (r'^accounts/login/$', 'login', {'template_name': 'ui/login.html'}),
    (r'^accounts/logout/$', 'logout', {'template_name': 'ui/logout.html'}),
)

urlpatterns += patterns('geppetto.ui.views.general',
    ('^$', 'root', {}, 'root'),

    ('^unassigned_workers_list$', 'unassigned_workers_list', {},
     'unassigned_workers_list'),

    (r'^', include('geppetto.ui.views.install.urls')),
    (r'^', include('geppetto.ui.views.config.urls')),
    (r'^', include('geppetto.ui.views.upgrade.urls')),

    (r'^(?P<page_name>[a-z_]+)$', 'common', {}, 'common')
)
