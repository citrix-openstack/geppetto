get_ip_address()
{
    /sbin/ip -o -4 addr show dev "$1" | sed -e 's,.*inet \([^/]*\).*,\1,'
}
