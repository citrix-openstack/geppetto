from django.conf.urls.defaults import patterns

urlpatterns = patterns('geppetto.ui.views.config',
    ('^network_create',
                'nova.network.network_create', {}, 'network_create'),
    ('^floating_create',
                'nova.network.floating_create', {}, 'floating_create'),
)
