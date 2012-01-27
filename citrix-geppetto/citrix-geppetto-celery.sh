GEPPETTO_USER=geppetto
export PYTHON_EGG_CACHE="/tmp/$GEPPETTO_USER/PYTHON_EGG_CACHE"
export GEPPETTO_DB=/var/lib/geppetto/sqlite3.db~

. /etc/rc.d/init.d/functions

pidfile="/var/run/geppetto/$name.pid"
lockfile="/var/lock/subsys/citrix-geppetto-$name"
logfile="/var/log/geppetto/$name.log"

[ -f "/etc/sysconfig/citrix-geppetto" ] && . "/etc/sysconfig/citrix-geppetto"


start() {
    echo -n "Starting citrix-geppetto-$name: "
    daemonize -u "$GEPPETTO_USER" -l "$lockfile" -a -e "$logfile" \
              "/usr/bin/python2.6" "/usr/lib/python2.6/site-packages/geppetto/manage.py" $name --pidfile="$pidfile"
    retval=$?
    [ $retval -eq 0 ] && touch "$lockfile"
    [ $retval -eq 0 ] && success || failure
    echo
    return $retval
}

stop() {
    echo -n "Stopping citrix-geppetto-$name: "
    killproc -p "$pidfile" "/usr/bin/python2.6"
    retval=$?
    rm -f "$lockfile"
    echo   
    return $retval
}

restart() {
    stop
    start
}

rh_status() {
    status -p "$pidfile" "/usr/bin/python2.6"
}

rh_status_q() {
    rh_status &> /dev/null
}

setup() {
    if [[ ! -e "$GEPPETTO_DB" && "$VPX_MASTER_DB_BACKEND" == "sqlite3" ]]
    then
        echo "Please ensure the geppetto database has been created. Please start citrix-geppetto first."
        exit 42
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
