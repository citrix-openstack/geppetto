from django.conf.urls.defaults import patterns

urlpatterns = patterns('geppetto.ui.views.upgrade',
    ('^upgrade_node', 'upgrade_node.select_role', {}, 'select_role'),
    ('^select_vpx', 'upgrade_node.select_vpx', {}, 'select_vpx'),
    ('^confirm_vpx', 'upgrade_node.confirm_vpx', {}, 'confirm_vpx'),
    ('^migrate_vpx', 'upgrade_node.migrate_vpx', {}, 'migrate_vpx'),
)
