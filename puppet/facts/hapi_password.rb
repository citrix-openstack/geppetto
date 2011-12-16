# This has weight 100 because it has to run first.
# All the goodies like weights, timeouts and caching require 
# a newer version of Facter. Comment these out for now. 
Facter.add("host_password_status") do
        # has_weight 100
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/hapi-check --password_status 2> /dev/null}.chomp
        end
end