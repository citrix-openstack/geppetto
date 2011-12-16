Facter.add("host_fqdn") do
        # has_weight 90
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get hostname 2> /dev/null}.chomp
        end
end

Facter.add("host_ip") do
        # has_weight 91
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get address 2> /dev/null}.chomp
        end
end

Facter.add("host_type") do
        # has_weight 93
        # timeout = 15       
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get virt-type 2> /dev/null}.chomp
        end
end

Facter.add("host_version") do
        # has_weight 94
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get software_version product_version 2> /dev/null}.chomp
        end
end

Facter.add("host_cpu_count") do
        # has_weight 80
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get cpu_info cpu_count 2> /dev/null}.chomp
        end
end

Facter.add("host_memory_total") do
        # has_weight 81
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get metrics memory_total 2> /dev/null}.chomp
        end
end

Facter.add("host_memory_free") do
        # has_weight 82
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get metrics memory_free 2> /dev/null}.chomp
        end
end

Facter.add("host_local_storage_size") do
        # has_weight 70 
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get local_storage physical_size 2> /dev/null}.chomp
        end
end

Facter.add("host_local_storage_utilisation") do
        # has_weight 71
        # timeout = 15
        setcode do
                %x{/usr/local/bin/geppetto/os-vpx/host-details-get local_storage physical_utilisation}.chomp
        end
end
