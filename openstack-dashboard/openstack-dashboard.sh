DASHBOARD_USER=root
# Note PYTHON_EGG_CACHE is overridden lower down, when we're running Python
# directly (i.e. not through daemonize).
export PYTHON_EGG_CACHE="/tmp/$DASHBOARD_USER/PYTHON_EGG_CACHE"
export DASHBOARD_DB=/var/lib/dashboard/dashboard_openstack.sqlite3

. /etc/rc.d/init.d/functions

pidfile="/var/run/dashboard/dashboard.pid"
lockfile="/var/lock/subsys/openstack-dashboard"

[ -f "/etc/sysconfig/openstack-dashboard" ] && . "/etc/sysconfig/openstack-dashboard"

OPTIONS="$OPTIONS"

start() {
    echo -n "Starting openstack-dashboard: "
    daemonize -p "$pidfile" -u "$DASHBOARD_USER" -l "$lockfile" \
              -a -e "/var/log/dashboard/dashboard-stderr.log" "/usr/bin/openstack-dashboard" $OPTIONS
    retval=$?
    [ $retval -eq 0 ] && touch "$lockfile"
    [ $retval -eq 0 ] && success || failure
    echo
    return $retval
}

stop() {
    echo -n "Stopping openstack-dashboard: "
    killproc -p "$pidfile" "/usr/bin/openstack-dashboard"
    retval=$?
    rm -f "$lockfile"
    echo
    ps aux | grep runserver | grep dashboard | awk '{ print $2 }' | xargs kill -9 2> /dev/null
    return $retval
}

restart() {
    stop
    start
}

rh_status() {
    status -p "$pidfile" "/usr/bin/openstack-dashboard"
}

rh_status_q() {
    rh_status &> /dev/null
}

setup() {
    if [[ ! -e "$DASHBOARD_DB" ]]
    then
        cd /var/lib/dashboard/ > /dev/null
        echo -n "No Database detected, creating..."
        export PYTHON_EGG_CACHE="/tmp/$(whoami)/PYTHON_EGG_CACHE"
        python26 /usr/lib/python2.6/site-packages/dashboard/manage.py syncdb --noinput
        export PYTHON_EGG_CACHE="/tmp/$DASHBOARD_USER/PYTHON_EGG_CACHE"
        cd - > /dev/null
        echo "done!"
    fi  
}

case "$1" in
    start)
        rh_status_q && exit 0
        setup
        $1
        ;;
    stop)
        rh_status_q || exit 0
        $1
        ;;
    restart)
        $1
        ;;
    reload)
        ;;
    status)
        rh_status
        ;;
    condrestart|try-restart)
        rh_status_q || exit 0
        restart
        ;;
    *)
        echo $"Usage: $0 {start|stop|status|restart|condrestart|try-restart}"
        exit 2
esac
exit $?
