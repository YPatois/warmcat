#!/bin/bash

ping -c 1 -W 2 192.168.1.254 >& /dev/null

if [ $? -eq 0 ]; then
    exit 0
else
    ifdown wlan1
    sleep 1
    ifup wlan1
fi