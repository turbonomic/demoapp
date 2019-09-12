#!/bin/bash


API_SERVICE_IP=${API_SERVICE_IP:-localhost}
LOCUST_MODE=${LOCUST_MODE:-standalone}

echo "$API_SERVICE_IP"

export TWEET_CONTENT_FILE='./files/reddit_comments_200703.txt'

locust -f locustfile.py --host=http://$API_SERVICE_IP:8699
