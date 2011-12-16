/* To ensure that configuration files are updated before any service
   starts, when adding config classes make sure to follow this pattern:

class your-component-config {
  conf { 'your-compontent':
    filename => 'path_to_file',
    config => "file_content",
  }
}
*/

define conf($filename, $config) {
  file { "$filename":
    content => "$config",
    before => Class["running-services"],
  }
}

class cert-config {
  conf { 'cert':
    filename => '/etc/openstack/cert',
    config => "CRED_CERT_C='$CRED_CERT_C'
               \nCRED_CERT_ST='$CRED_CERT_ST'
               \nCRED_CERT_L='$CRED_CERT_L'
               \nCRED_CERT_O='$CRED_CERT_O'
               \nCRED_CERT_OU='$CRED_CERT_OU'",
  }
}

class compute-api-config {
  conf { 'compute-api':
    filename => '/etc/openstack/compute-api',
    config => "COMPUTE_API_HOST=$COMPUTE_API_HOST",
  }
}

class dashboard-config {
  conf { 'dashboard':
    filename => '/etc/openstack/dashboard',
    config => "DASHBOARD_ACCESS='$DASHBOARD_ACCESS'
               \nDASHBOARD_SECRET='$DASHBOARD_SECRET'
               \nDASHBOARD_ADMIN='$DASHBOARD_ADMIN'
               \nDASHBOARD_PROJECT='$DASHBOARD_PROJECT'
               \nDASHBOARD_SMTP_SVR='$DASHBOARD_SMTP_SVR'
               \nDASHBOARD_SMTP_USR='$DASHBOARD_SMTP_USR'
               \nDASHBOARD_SMTP_PWD='$DASHBOARD_SMTP_PWD'",
  }
}

# This is special
class geppetto-vpx-config {
  conf { 'geppetto-vpx':
    filename => '/etc/openstack/geppetto',
    config => "VPX_LABEL_PREFIX='$VPX_LABEL_PREFIX'
               \nVPX_DESCRIPTION='$VPX_DESCRIPTION'
               \nVPX_TAGS=[$VPX_TAGS]",
  }
  exec { "geppetto-properties-update":
    subscribe => [File["/etc/openstack/geppetto"],
                  File["/etc/openstack/hapi"]],
    refreshonly => true,
    require => Class["hapi-config"],
  }
}

class geppetto-syslog-config {
  conf { 'syslog':
    filename => '/etc/openstack/syslog',
    config => "VPX_LOGGING_COLLECTOR=$VPX_LOGGING_COLLECTOR
    		   \nVPX_LOGGING_LEVEL=$VPX_LOGGING_LEVEL",
  }
  exec { "configure-vpx-logging":
    subscribe => File["/etc/openstack/syslog"],
    refreshonly => true,
  }
  service { 'rsyslog':
    enable => "true",
    ensure => "running",
    hasstatus => "true",
    require => Exec["configure-vpx-logging"],
    subscribe => File["/etc/openstack/syslog"],
  }
}

class glance-config {
  conf { 'glance':
    filename => '/etc/openstack/glance',
    config => "GLANCE_HOSTNAME=$GLANCE_HOSTNAME
               \nAPI_BIND_HOST=$API_BIND_HOST
               \nAPI_BIND_PORT=$API_BIND_PORT
               \nREGISTRY_BIND_HOST=$REGISTRY_BIND_HOST
               \nREGISTRY_BIND_PORT=$REGISTRY_BIND_PORT",
  }
}

class glance-store-config {
  conf { 'glance-store':
    filename => '/etc/openstack/glance-store',
    config => "GLANCE_STORE=$GLANCE_STORE
               \nGLANCE_FILE_STORE_SIZE_GB=$GLANCE_FILE_STORE_SIZE_GB
               \nGLANCE_SWIFT_ADDRESS=$GLANCE_SWIFT_ADDRESS
               \nGLANCE_SWIFT_USER=$GLANCE_SWIFT_USER
               \nGLANCE_SWIFT_STORE_KEY=$GLANCE_SWIFT_STORE_KEY",
  }
}

class guest-network-config {
  conf { 'guest-network':
    filename => '/etc/openstack/guest-network',
    config => "GUEST_NETWORK_BRIDGE='$GUEST_NETWORK_BRIDGE'
               \nGUEST_NETWORK_DNS='$GUEST_NETWORK_DNS'
               \nNETWORK_MANAGER=$NETWORK_MANAGER
               \nCOMPUTE_NETWORK_DRIVER=$COMPUTE_NETWORK_DRIVER
               \nCOMPUTE_VLAN_INTERFACE=$COMPUTE_VLAN_INTERFACE
               \nNETWORK_NETWORK_DRIVER=$NETWORK_NETWORK_DRIVER
               \nNETWORK_VLAN_INTERFACE=$BRIDGE_INTERFACE
               \nBRIDGE_INTERFACE=$BRIDGE_INTERFACE
               \nPUBLIC_INTERFACE=$PUBLIC_INTERFACE
               \nFIREWALL_DRIVER=$FIREWALL_DRIVER
               \nFLAT_INJECTED=$FLAT_INJECTED
               \nMULTI_HOST=$MULTI_HOST"
  }
}

class hapi-config {
  conf { 'hapi':
    filename => '/etc/openstack/hapi',
    config => "HAPI_USER=$HAPI_USER
               \nHAPI_PASS='$HAPI_PASS'
               \nVMWAREAPI_WSDL_LOC=$VMWAREAPI_WSDL_LOC",
  }
}

class host-config {
  conf { 'host':
    filename => '/etc/openstack/host',
    config => "HOST_GUID=$HOST_GUID",
  }
}

class keystone-config {
  conf { 'keystone':
    filename => '/etc/openstack/keystone',
    config => "KEYSTONE_HOST=$KEYSTONE_HOST
               \nKEYSTONE_SUPERUSER_NAME=$KEYSTONE_SUPERUSER_NAME
               \nKEYSTONE_SUPERUSER_PASS=$KEYSTONE_SUPERUSER_PASS
               \nKEYSTONE_SUPERUSER_TOKEN=$KEYSTONE_SUPERUSER_TOKEN
               \nKEYSTONE_SUPERUSER_TENANT=$KEYSTONE_SUPERUSER_TENANT",
  }
}

class memcached {
  #TODO
}

class mysql-config {
  conf { 'mysql':
    filename => '/etc/openstack/mysql',
    config => "MYSQL_HOST=$MYSQL_HOST
               \nMYSQL_USER=$MYSQL_USER
               \nMYSQL_PASS=$MYSQL_PASS
               \nMYSQL_DBS='$MYSQL_DBS'",
  }
}

class netscaler-config {
  conf { 'netscaler':
    filename => '/etc/openstack/netscaler',
    config => "NS_VPX_HOST=$NS_VPX_HOST
               \nNS_VPX_PORT=$NS_VPX_PORT
               \nNS_VPX_USER=$NS_VPX_USER
               \nNS_VPX_PASS=$NS_VPX_PASS
               \nNS_VPX_VIPS=$NS_VPX_VIPS",
  }
}

class networking-config {
  conf { 'networking':
    filename => '/etc/openstack/networking',
    config => "PRIVATE_NIC=$PRIVATE_NIC",
  }
}

class nova-ajax-console-proxy-config {
  conf { 'nova-ajax-console-proxy':
    filename => '/etc/openstack/nova-ajax-console-proxy',
    config => "NOVA_AJAX_CONSOLE_PROXY_BIND_INTERFACE=$NOVA_AJAX_CONSOLE_PROXY_BIND_INTERFACE
             \nNOVA_AJAX_CONSOLE_PROXY_BIND_PORT=$NOVA_AJAX_CONSOLE_PROXY_BIND_PORT",
  }
}

class nova-ajax-console-public-config {
  conf { 'nova-ajax-console-public':
    filename => '/etc/openstack/nova-ajax-console-public',
    config => "NOVA_AJAX_CONSOLE_PUBLIC_URL=$NOVA_AJAX_CONSOLE_PUBLIC_URL
             \nNOVA_AJAX_CONSOLE_PUBLIC_URL_COMPUTED=$NOVA_AJAX_CONSOLE_PUBLIC_URL_COMPUTED"
  }
}

class rabbitmq-config {
  conf { 'rabbitmq':
    filename => '/etc/openstack/rabbitmq',
    config => "RABBIT_HOST=$RABBIT_HOST
               \nRABBIT_PORT=$RABBIT_PORT
               \nRABBIT_USER=$RABBIT_USER
               \nRABBIT_PASS=$RABBIT_PASS",
  }
}

class scheduler-config {
  conf { 'scheduler':
    filename => '/etc/openstack/scheduler',
    config => "SCHEDULER_COMPUTE_DRIVER=$SCHEDULER_COMPUTE_DRIVER
               \nSCHEDULER_VOLUME_DRIVER=$SCHEDULER_VOLUME_DRIVER
               \nSCHEDULER_DEFAULT_HOST_FILTER=$SCHEDULER_DEFAULT_HOST_FILTER",
  }
}

class swift-config {
  conf { 'swift':
    filename => '/etc/openstack/swift',
    config => "SWIFT_PROXY_ADDRESS=$SWIFT_PROXY_ADDRESS
               \nSWIFT_HASH_PATH_SUFFIX=$SWIFT_HASH_PATH_SUFFIX",
  }
}

class swift-disks-config {
  conf { 'swift-disks':
    filename => '/etc/openstack/swift-store',
    config => "SWIFT_DISK_SIZE_GB=$SWIFT_DISK_SIZE_GB
               \nSWIFT_DEVICES='$SWIFT_DEVICES'",
  }
}

# This is special
class swift-rings-config {
    file { "/var/lib/swift/account.ring.gz":
        source  => 'puppet:///swift/account.ring.gz',
        owner   => 'swift',
        group   => 'swift',
        mode    => '644',
        before => Class["running-services"],
    }
    file { "/var/lib/swift/container.ring.gz":
        source  => 'puppet:///swift/container.ring.gz',
        owner   => 'swift',
        group   => 'swift',
        mode    => '644',
        before => Class["running-services"],
    }
    file { "/var/lib/swift/object.ring.gz":
        source  => 'puppet:///swift/object.ring.gz',
        owner   => 'swift',
        group   => 'swift',
        mode    => '644',
        before => Class["running-services"],
    }
}

class volume-config {
  conf { 'volume':
    filename => '/etc/openstack/volume',
    config => "VOLUME_DISK_SIZE_GB=$VOLUME_DISK_SIZE_GB
               \nTARGET_HOST=$TARGET_HOST \
               \nTARGET_PORT=$TARGET_PORT \
               \nIQN_PREFIX=$IQN_PREFIX \
               \nISCSI_IP_PREFIX=$ISCSI_IP_PREFIX \
               \nVOLUME_DRIVER=$VOLUME_DRIVER \
               \nUSE_LOCAL_VOLUMES=$USE_LOCAL_VOLUMES",
    notify => Service['openstack-nova-volume', 'openstack-nova-compute'],
  }
}

class os-vpx-maintenance-config {
	conf { 'maintenance':
	    filename => '/var/lib/geppetto/os-vpx-task',
	    config => "VPX_MAINTENANCE_TASK=$VPX_MAINTENANCE_TASK",
	  }
}
