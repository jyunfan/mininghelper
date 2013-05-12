#!/bin/bash
# Reset cgminer when hash rate below specific threshold.

IP=127.0.0.1
PORT=4028
THRESH=20000
DEVICE=1

while true
do
  # Get metrics of all devices
  RATE=$(echo -n 'devs' | nc ${IP} ${PORT} | egrep -a -o 'MHS 5s=[0-9]+' | egrep -a -o '[0-9]+$')
  # Get the specific metric we want
  RATE=$(echo $RATE | awk "{print "'$'"$DEVICE}")
  echo "RATE=$RATE" $(date)
  if [ $RATE -lt $THRESH ]; then
    echo "Reset" $(date)
    echo -n 'restart' | nc ${IP} ${PORT}
    sleep 60
  fi
  sleep 10
done
