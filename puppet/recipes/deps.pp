/* To ensure that services are initialized correctly, when adding init
   classes, make sure to follow this pattern:

class ensure-your-component-init-run {
  init { 'confirm-your-component-initialized':
    cmd => "your-init-command",
    state => "/var/lib/geppetto/your-component-init-run",
    configs => ['config1', 'config2', ...],
    notify => ['class1', 'class2', ...],
  }
}
*/

define init($cmd, $state, $configs=[], $subscribers=[]) {
  exec { "$cmd":
    creates => "$state",
    before => Class["running-services"],
    require => Class[$configs],
    notify => Class[$subscribers],
  }
}

class ensure-image-container-init-run {
  init { 'confirm-image-container-initialized':
    cmd => "image-container-init $IMG_CONTAINER_SIZE \
                                 $IMG_CONTAINER_OWNER",
    state => "/var/lib/geppetto/image-container-init-run",
    configs => 'hapi-config',
  }
}

class ensure-mysql-init-run {
  init { 'confirm-mysql-initialized':
    cmd => "database-init",
    state => "/var/lib/geppetto/database-init-run",
    configs => ['mysql-config',
                'networking-config'],
  }
}

class ensure-ns-vpx-provision-init-run {
  init { 'confirm-ns-vpx-provision-initialized':
    cmd => "/usr/bin/os-vpx-spawn-lbaas-vm $NS_VPX_VM_TEMPLATE_NAME \
                                           $NS_VPX_VM_MAC_ADDRESS \
                                           $NS_VPX_VM_NETWORK_BRIDGE",
    state => "/var/lib/geppetto/ns-vpx-init-run",
    configs => 'hapi-config',
  }
}

class ensure-glance-init-run {
  init { 'confirm-glance-initialized':
    cmd => "glance-api-init",
    state => "/var/lib/geppetto/glance-init-run",
    configs => 'glance-store-config',
   }
}

class configure-glance-locations {
   exec { "glance-location-update":
      command => "glance-location-update",
      subscribe => File["/etc/openstack/keystone"],
      require => Class["keystone-config", "restarted-services"],
      tries => 8,
      try_sleep => 10,
      creates => "/var/lib/geppetto/glance-location-update-run",
   }
}

class ensure-nova-volume-init-run {
  init { 'confirm-nova-volume-initialized':
    cmd => "nova-volume-init",
    state => "/var/lib/geppetto/nova-volume-init-run",
    configs => 'volume-config',
  }
}

class ensure-swift-init-run {
  init { 'confirm-swift-initialized':
    cmd => "attach-swift-disk",
    state => "/var/lib/geppetto/swift-init-run",
    configs => 'swift-disks-config',
  }
}

class ensure-swift-ring-builder-init-run {
  init { 'confirm-swift-ring-builder-initialized':
    cmd => "swift-ring-builder-init $SWIFT_NODES_IPS",
    state => "/var/lib/geppetto/swift-ring-builder-init-run",
  }
}

class ensure-openstack-dashboard-init-run {
  init { 'confirm-openstack-dashboard-init-run':
    cmd => "openstack-dashboard-init",
    state => "/var/lib/geppetto/openstack-dashboard-init-run",
    configs => ['dashboard-config',
                'keystone-config'],
  }
}

class configure-dashboard-settings {
   exec { "dashboard-settings-update":
      command => "dashboard-settings-update",
      subscribe => File["/etc/openstack/dashboard",
                        "/etc/openstack/keystone"],
      refreshonly => true,
      require => Class["ensure-openstack-dashboard-init-run"],
      before => Class["running-services"],
   }
}

class ensure-keystone-init-run {
  init { 'confirm-keystone-init-run':
    cmd => "keystone-init",
    state => "/var/lib/geppetto/keystone-init-run",
    configs => ['keystone-config'],
    subscribers => ['configure-keystone-endpoints'],
  }
}

class configure-keystone-endpoints {
   exec { "keystone-endpoint-update":
      command => "keystone-endpoint-update",
      subscribe => File["/etc/openstack/glance",
                        "/etc/openstack/keystone",
                        "/etc/openstack/swift",
                        "/etc/openstack/compute-api"],
      refreshonly => true,
      require => Class["restarted-services"],
      tries => 6,
      try_sleep => 5,
   }
}

define build-ifcfg( $device, $mode, $ip, $netmask, $host_network) {
   file { "/etc/sysconfig/network-scripts/ifcfg-$device":
      owner => root,
      group => root,
      mode => 664,
      content => $mode ? {
          dhcp => "DEVICE=$device \
                   \nBOOTPROTO=dhcp \
                   \nONBOOT=yes \
                   \nNOZEROCONF=yes \
                   \nGEPPETTO_HOST_NETWORK=$host_network",
          static => "DEVICE=$device \
                     \nBOOTPROTO=static \
                     \nONBOOT=yes \
                     \nIPADDR=$ip \
                     \nNETMASK=$netmask \
                     \nNOZEROCONF=yes \
                     \nGEPPETTO_HOST_NETWORK=$host_network",
          noip => "DEVICE=$device \
                   \nBOOTPROTO=static \
                   \nONBOOT=yes \
                   \nGEPPETTO_HOST_NETWORK=$host_network",                     
          default => "DEVICE=$device \
                      \nBOOTPROTO=static \
                      \nONBOOT=no",
      },
      before => Class["running-services"],
   }
} 

define update-vif( $device ) {
   exec { "os-vpx-update-vif-$title":
      command => "vif-update $device",
      subscribe => File["/etc/sysconfig/network-scripts/ifcfg-$device"],
      refreshonly => true,
      before => Exec["Reset_$title"]
   }
}

define reset-vif( $device) {
   exec { "ifdown $device; ifup $device":
      alias => "Reset_$title",
      path => "/sbin",
      subscribe => File["/etc/sysconfig/network-scripts/ifcfg-$device"],
      refreshonly => true,
      before => Class["running-services"],
   }
}
   
class configure-guest-nw-vif {   
   build-ifcfg { "guest-$BRIDGE_INTERFACE":
        device => $BRIDGE_INTERFACE,
        mode => $GUEST_NW_VIF_MODE,
   		ip => $GUEST_NW_VIF_IP,
   		netmask => $GUEST_NW_VIF_NETMASK,
   		host_network => $GUEST_NETWORK_BRIDGE,
   }
   update-vif { "guest-$BRIDGE_INTERFACE":
   		 device => $BRIDGE_INTERFACE,
   }
   reset-vif { "guest-$BRIDGE_INTERFACE":
   		 device => $BRIDGE_INTERFACE, 
   }
}

class configure-public-vif {   
   build-ifcfg { "pub-$PUBLIC_INTERFACE":
        device => $PUBLIC_INTERFACE,
        mode => $PUBLIC_NW_VIF_MODE,
   		ip => $PUBLIC_NW_VIF_IP,
   		netmask => $PUBLIC_NW_VIF_NETMASK,
   		host_network => $PUBLIC_NETWORK_BRIDGE,
   }
   update-vif { "pub-$PUBLIC_INTERFACE":
   		device => $PUBLIC_INTERFACE, 
   }
   reset-vif { "pub-$PUBLIC_INTERFACE": 
   		device => $PUBLIC_INTERFACE,
   }
}

class ensure-geppetto-init-run {
  init { 'confirm-geppetto-initialized':
    cmd => "geppetto-init",
    state => "/var/lib/geppetto/geppetto-init-run",
    configs => 'geppetto-backend-config',
   }
}

