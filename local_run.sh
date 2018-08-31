#!/bin/bash

# kill -- -$$ sends a SIGTERM to the whole process group, thus killing also descendants.
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

mkdir -p logs

echo '' > logs/log.txt

python http_server/http_server.py >> logs/log.txt &

python user_service/user_service_grpc.py  >> logs/log.txt &

python tweet_service/tweet_service_grpc.py >> logs/log.txt &

python friend_service/friend_service_grpc.py >> logs/log.txt &

tail -f logs/log.txt

