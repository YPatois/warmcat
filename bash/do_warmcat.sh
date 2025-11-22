#!/bin/bash

SCRIPTBASEDIR=$(dirname $(readlink -f $0))
export SCRIPTBASEDIR

echo "starting warmcat bash loop"
cd $SCRIPTBASEDIR/../python/
ls -l
while true; do
    echo `date` " warming for one hour"
    ./warmcat.py
    sleep 1
done
