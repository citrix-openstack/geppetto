GEPPETTO_USER=geppetto
# Note PYTHON_EGG_CACHE is overridden lower down, when we're running Python
# directly (i.e. not through daemonize).
export PYTHON_EGG_CACHE="/tmp/$GEPPETTO_USER/PYTHON_EGG_CACHE"
export GEPPETTO_DB="/var/lib/geppetto/sqlite3.db~"
export GEPPETTO_PATH="/usr/lib/python2.6/site-packages/geppetto"
export GEPPETTO_MANAGE="$GEPPETTO_PATH/manage.py"
export GEPPETTO_SETTINGS="$GEPPETTO_PATH/settings.py"

. /etc/rc.d/init.d/functions

flagfile="/etc/geppetto/geppetto.conf"
pidfile="/var/run/geppetto/geppetto.pid"
lockfile="/var/lock/subsys/citrix-geppetto"

[ -f "/etc/sysconfig/citrix-geppetto" ] && . "/etc/sysconfig/citrix-geppetto"

OPTIONS="$OPTIONS" # no flag file at the moment --flagfile=$flagfile

start() {
    echo -n "Starting citrix-geppetto: "
    daemonize -p "$pidfile" -u "$GEPPETTO_USER" -l "$lockfile" \
              -a -e "/var/log/geppetto/geppetto.log" "/usr/bin/geppetto" $OPTIONS
    retval=$?
    [ $retval -eq 0 ] && touch "$lockfile"
    [ $retval -eq 0 ] && success || failure
    echo
    return $retval
}

stop() {
    echo -n "Stopping citrix-geppetto: "
    killproc -p "$pidfile" "/usr/bin/geppetto"
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
    status -p "$pidfile" "/usr/bin/geppetto"
}

rh_status_q() {
    rh_status &> /dev/null
}

splash() {
    echo "------------------------------------------------------------"
    echo "   DEVELOPMENT SERVER AVAILABLE AT: http://$INTF:$PORT"
    echo "------------------------------------------------------------"
}

reset() {
    while true; do 
        if [ "$1" == "--force" ]
        then
            REPLY=y
        else
            read -p "This will destroy the current Geppetto DB. Are you sure (y/n)? "
        fi
        if [ "$REPLY" == "y" -o "$REPLY" == "Y" ]
        then
            service citrix-geppetto stop
            rm $GEPPETTO_DB
            service citrix-geppetto start
            echo
            echo "Geppetto DB has been reset!"
            TIME=`cat /etc/puppet/puppet.conf | grep runinterval | awk '{ print $3 }'`
            echo "Client nodes will re-register with the master in less than ${TIME} seconds."
            echo
            break
        elif [ "$REPLY" == "n" -o "$REPLY" == "N" ]
        then
            echo "Exit without making changes!"
            break
        fi
    done
}

setup() {
    if [[ ! -e "$GEPPETTO_DB" ]]
    then
        cd /var/lib/geppetto/ > /dev/null
        echo "No Database detected, creating one."
        export PYTHON_EGG_CACHE="/tmp/$(whoami)/PYTHON_EGG_CACHE"
        python26 $GEPPETTO_MANAGE syncdb --noinput --verbosity=0
        python26 $GEPPETTO_MANAGE migrate
        python26 $GEPPETTO_MANAGE geppettodb init
        export PYTHON_EGG_CACHE="/tmp/$GEPPETTO_USER/PYTHON_EGG_CACHE"
        chown geppetto.geppetto $GEPPETTO_DB
        cd - > /dev/null
    else
        export PYTHON_EGG_CACHE="/tmp/$(whoami)/PYTHON_EGG_CACHE"
        changes=$(python26 $GEPPETTO_MANAGE migrate --list | grep -w "( )" | wc -l)
        if [ $changes -gt 0 ]
        then
            echo "A newer version of Geppetto has been detected. Applying changes to the database." 
            python26 $GEPPETTO_MANAGE migrate geppetto.core
        fi
        export PYTHON_EGG_CACHE="/tmp/$GEPPETTO_USER/PYTHON_EGG_CACHE"
    fi
}

debug()
{
    flag=$2
    if [ "$flag" == "--debug" ]
    then
      flag="True"
    else
      flag="False"
    fi
    sed -e "s,^DEBUG = .*,DEBUG = $flag," -i "$GEPPETTO_SETTINGS"
}

case "$1" in
    start)
        debug $@
        rh_status_q && exit 0
        setup
        $1
        splash
        ;;
    stop)
        rh_status_q || exit 0
        $1
        ;;
    restart)
        debug $@
        $1
        ;;
    reload)
        ;;
    status)
        rh_status
        ;;
    reset)
        reset $2
        ;;
    condrestart|try-restart)
        rh_status_q || exit 0
        restart
        ;;
    *)
        echo $"Usage: $0 {start [--debug]|stop|status|restart [--debug]|condrestart|try-restart|reset [--force]}"
        exit 2
esac
exit $?