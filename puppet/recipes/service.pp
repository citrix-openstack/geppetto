class openstack-role-set {
    include running-services,
            stopped-services,
            restarted-services,
            absent-files
}

class running-services {

    if $running_services
    {
        notice("Running services: ${running_services}")
        service { $running_services:
            enable => true,
            ensure => running,
            hasstatus => true,
            before => Class["stopped-services"],
        }
    }
}

class stopped-services {

    if $stopped_services
    {
        notice("Stopping services: ${stopped_services}")
        service { $stopped_services:
            enable => false,
            ensure => stopped,
            hasstatus => true,
            before => Class["restarted-services"],
        }
    }
}

class restarted-services {

    define restart-service ( ) {
        exec { "service ${name} restart": path => "/sbin", }
    }

    if $VPX_RESTART_SERVICES
    {
        notice("Restarting services: ${VPX_RESTART_SERVICES}")
        restart-service { $VPX_RESTART_SERVICES: }
    }
}

class absent-files {
   if $VPX_ABSENT_FILES
    {
        info("Ensure that these files do not exist: ${VPX_ABSENT_FILES}")
        file { $VPX_ABSENT_FILES:
            ensure => absent,
        }
    }
}

class os-vpx-maintenance {
    include os-vpx-maintenance-config
}
