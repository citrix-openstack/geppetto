from django.conf.urls.defaults import patterns


_standard_patterns = [
    'checklist.install_checklist',
    'hypervisor.setup_password',
    'identity.setup_identity',
    'images_upload.setup_image_container',
    'imaging.setup_imaging',
    'lbaas_setup.configure_lbaas',
    'lbaas_setup.lbservice',
    'lbaas_setup.lbservice_delete',
    'lbaas_setup.lbservice_finish',
    'lbaas_setup.lbservice_info',
    'lbaas_setup.lbservice_list',
    'lbaas_setup.lbservice_select_vms',
    'management.setup_complete',
    'management.setup_network',
    'management.setup_network_worker',
    'management.setup_network_service',
    'management.setup_network_public_vif',
    'management.setup_network_public_vif_static',
    'management.setup_nova_ajax_console_proxy',
    'management.setup_nova_api',
    'management.setup_scheduler',
    'nova_other.add_compute_node',
    'rabbitmq_mysql.setup_mysql',
    'rabbitmq_mysql.setup_mysql_external',
    'rabbitmq_mysql.setup_rabbitmq',
    'rabbitmq_mysql.setup_rabbitmq_external',
    'scaleout.scaleout_choose_role',
    'scaleout.scaleout_choose_worker',
    'swift.setup_swift_api',
    'swift.setup_swift_hash_path_suffix',
    'swift.setup_swift_progress',
    'swift.setup_swift_start',
    'swift.setup_swift_storage',
    'swift.setup_swift_storage_size',
    ]


urlpatterns = []
for p in _standard_patterns:
    f = p.split('.')[-1]
    urlpatterns += patterns('geppetto.ui.views.install',
                            ('^%s$' % f, p, {}, f))


urlpatterns += patterns('geppetto.ui.views.install',
    ('^add_workers_for_supporting_roles$',
     'rabbitmq_mysql.master_add_workers_for_supporting_roles', {},
     'add_workers_for_supporting_roles'),
    ('^progress_mysql_rabbitmq$', 'rabbitmq_mysql.progress', {},
     'progress_mysql_rabbitmq'),

    ('^setup_block_storage_worker$', 'block_storage.setup_worker', {},
     'setup_block_storage_worker'),
    ('^setup_block_storage_iscsi$', 'block_storage.setup_iscsi', {},
     'setup_block_storage_iscsi'),
    ('^setup_block_storage_sm$', 'block_storage.setup_sm', {},
     'setup_block_storage_sm'),
    ('^setup_block_complete$', 'block_storage.setup_block_complete', {},
     'setup_block_complete'),

    ('^publish_service$', 'publish_service.publish', {}, 'publish_service'),
    ('^publish_service_static_network$', 'publish_service.static_network', {},
     'publish_service_static_network'),

    ('^images_upload$', 'images_upload.select_and_upload', {},
     'images_upload'),
    ('^images_register$', 'images_upload.nova_manage_register', {},
     'images_register'),
)
