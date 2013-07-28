#!/bin/bash
# Reboot system when hash rate below specific threshold.

IP=127.0.0.1
PORT=4028
THRESH=20000
DEVICE=1
LOG=/var/log/rebootcgminer.log

sleep 20

while true
do
  # Get metrics of all devices
  RATE=$(echo -n 'devs' | nc ${IP} ${PORT} | egrep -a -o 'MHS 5s=[0-9]+' | egrep -a -o '[0-9]+$')
  # Get the specific metric we want
  RATE=$(echo $RATE | awk "{print "'$'"$DEVICE}")
  echo "RATE=$RATE" $(date) >> $LOG
  # Reboot system if hash rate below the threshold
  if [ -z "$RATE" ] || [ $RATE -lt $THRESH ]; then
    echo "reboot at " $(date) >> $LOG
    shutdown -r now
  fi
  sleep 20
done
