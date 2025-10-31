#!/bin/bash

# Do forever
while true; do
    sensors >> ~/sensors.txt
    sleep 30
done
