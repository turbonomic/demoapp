#!/bin/bash

LOCUST="locust"
LOCUSTFILE=${LOCUSTFILE:-locustfile.py}
LOCUST_OPTS="-f locustfile.py --host=$TARGET_HOST"
LOCUST_MODE=${LOCUST_MODE:-standalone}
AUTOSTART=${AUTOSTART:-true}

if [[ "$LOCUST_MODE" = "master" ]]; then
    LOCUST_OPTS="$LOCUST_OPTS --master"
    if [[ $AUTOSTART = "true" ]]; then
      USERS=${USERS:-300}
      SPAWN_RATE=${SPAWN_RATE:-20}
      LOCUST_OPTS="$LOCUST_OPTS --autostart --users $USERS --spawn-rate $SPAWN_RATE"
    fi
elif [[ "$LOCUST_MODE" = "worker" ]]; then
    LOCUST_OPTS="$LOCUST_OPTS --worker --master-host=$LOCUST_MASTER"
fi

echo "$LOCUST $LOCUST_OPTS"

$LOCUST $LOCUST_OPTS
