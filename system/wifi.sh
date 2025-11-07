#! /bin/sh
### BEGIN INIT INFO
# Provides:          wifi
# Required-Start:  $network
# Required-Stop:
# Default-Start:     S
# Default-Stop:
# Short-Description: Wifi
# Description:       Wifi
#                    Wifi
### END INIT INFO

PATH=/sbin:/bin

. /lib/init/vars.sh
. /lib/lsb/init-functions

do_start () {
        ifdown wlan1
        sleep 1
        ifup wlan1
}

case "$1" in
  start|"")
        do_start
        ;;
  restart|reload|force-reload)
        echo "Error: argument '$1' not supported" >&2
        exit 3
        ;;
  stop)
        # No-op
        ;;
  status)
        exit 0
        ;;
  *)
        echo "Usage: wifi.sh [start|stop]" >&2
        exit 3
        ;;
esac

:

