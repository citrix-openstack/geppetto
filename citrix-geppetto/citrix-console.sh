#!/bin/bash

SYS_UUID_S="/sys/hypervisor/uuid"
SYS_UUID_D="/var/lib/geppetto/sys_uuid"
VPX_ROLE_F="/var/lib/geppetto/vpx_role"

# Switching eth1 ONBOOT to yes
sed -i -e "s/ONBOOT=no/ONBOOT=yes/g" /etc/sysconfig/network-scripts/ifcfg-eth1

# Determining whether the VM has changed
if [ -f "$SYS_UUID_D" ]
then
    sys_uuid_s=$(cat "$SYS_UUID_S")
    sys_uuid_d=$(cat "$SYS_UUID_D")
    # if the two uuids differ, the VM has changed and the role
    # may need to be re-established. So reset the role to trigger 
    # a new role auto-detection poll.
    if [ "$sys_uuid_s" != "$sys_uuid_d" ]
    then
        rm -f "$VPX_ROLE_F"
        cp "$SYS_UUID_S" "$SYS_UUID_D"
    fi
else
    # drop the vm uuid onto the data disk, this is 
    # useful to establish whether an 'old' data disk
    # has been attached to a 'new' VM
    cp "$SYS_UUID_S" "$SYS_UUID_D"
fi

case "$1" in
    start)
        python2.6 /usr/lib/python2.6/site-packages/geppetto/firstboot/XSConsole.py
        ;;
    stop)
        ;;
    restart)
        ;;
    reload)
        ;;
    status)
        ;;
    *)
        echo $"Usage: $0 {start|stop|status|restart|condrestart|try-restart}"
        exit 2
esac
exit $?
