import "classes/*"

Exec {
   logoutput => true,
   path => ["/usr/local/sbin/",
            "/usr/local/bin/",
            "/sbin/",
            "/bin/",
            "/usr/sbin/",
            "/usr/bin/",
            "/usr/local/bin/geppetto/",
            "/usr/local/bin/geppetto/os-vpx/",
            "/usr/local/bin/geppetto/init/",]
}
