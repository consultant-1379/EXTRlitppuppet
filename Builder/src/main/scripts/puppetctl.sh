#!/bin/bash
# Script to implement functions formerly in SysV init script
# and which cannot be handled by the systemd unit file.

. /etc/rc.d/init.d/functions

stop() {
    # Get the daemon pid if exists and kill any child processes of that pid
    # Originally added to init script for LITPCDS-11661
    # This function now called on systemctl stop puppet
    pidfile=/var/run/puppet/agent.pid
    [[ -f ${pidfile} ]] && daemonpid=$(cat ${pidfile})
    if [[ -n ${daemonpid} ]]; then
        pkill -TERM -P ${daemonpid} || :
        sleep 1 # grace period
        pgrep -P ${daemonpid} > /dev/null && (pkill -KILL -P ${daemonpid} || :)
    fi
    killproc -p ${pidfile} /usr/bin/puppet
    RETVAL=$?
    [ $RETVAL = 0 ] && rm -f ${pidfile}
}

case "$1" in
    stop)
        stop;
        ;;
    *)
        exit 2
        ;;
esac
exit $?
