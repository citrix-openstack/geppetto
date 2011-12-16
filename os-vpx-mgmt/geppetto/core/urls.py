from django.conf.urls.defaults import *

urlpatterns = patterns('geppetto.core.views',
                            (r'^report', 'report_service.process_report'),
                            (r'^facter', 'facter_service.svc'),
                            (r'^classifier', 'classifier_service.svc'),
                            (r'^geppetto/v1$', 'geppetto_service.svc'),
                            (r'^atlas', 'atlas_service.svc'),
)
