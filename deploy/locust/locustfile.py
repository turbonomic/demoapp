import os
from locust import HttpLocust, TaskSet, task
import random
from datetime import datetime
import logging

MAX_TWITTER_USER_ID = int(os.getenv('MAX_TWITTER_USER_ID', 101))
MAX_NUM_FOLLOWS = int(os.getenv('MAX_NUM_FOLLOWS', 50))
VISIT_RATE_TWEET = int(os.getenv('VISIT_RATE_TWEET', 1000))
VISIT_RATE_TIMELINE = int(os.getenv('VISIT_RATE_TIMELINE', 100))
VISIT_RATE_NEWSFEED = int(os.getenv('VISIT_RATE_NEWSFEED', 1000))
VISIT_RATE_FOLLOW = int(os.getenv('VISIT_RATE_FOLLOW', 10))
NEXT_REQUEST_MIN_WAIT_MS = int(os.getenv('NEXT_REQUEST_MIN_WAIT_MS', 1000))
NEXT_REQUEST_MAX_WAIT_MS = int(os.getenv('NEXT_REQUEST_MAX_WAIT_MS', 10000))

ENABLE_TIME_SLOT_PROBABILITY = os.getenv('ENABLE_TIME_SLOT_PROBABILITY', '0') != '0'
TIME_SLOT_PROBABILITY = list(map(lambda p:int(10*float(p)), os.getenv('TIME_SLOT_PROBABILITY', '1.0,0.7,0.4,0.1,0.4,0.7').split(',')))

def time_to_fire():
    if not ENABLE_TIME_SLOT_PROBABILITY:
        return True

    m = datetime.now().minute // 10
    p = TIME_SLOT_PROBABILITY[m]
    return p >= random.randint(1,10)

filename = os.getenv('TWEET_CONTENT_FILE', '/comments.txt')
comments = []
i = 0
with open(filename) as name_file:
    for line in name_file:
        i += 1
        comments.append(line)


class UserBehavior(TaskSet):
    def __init__(self, *args, **kwargs):
        super(UserBehavior, self).__init__(*args, **kwargs)

        self.user_id = str(random.randint(1,MAX_TWITTER_USER_ID))
        self.password = self.user_id
        self.tweet_endpoint = "/tweet"
        self.timeline_endpoint = "/timeline"
        self.newsfeed_endpoint = "/newsfeed"
        self.follows_endpoint = "/follows"

        if ENABLE_TIME_SLOT_PROBABILITY:
            logging.info("Time slot probability is enabled: %s", TIME_SLOT_PROBABILITY)

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def login(self):
        self.user_id = self.client.post("/setcookie", {"username": self.user_id, "password": self.password})

    @task(VISIT_RATE_TWEET)
    def tweet(self):
        if not time_to_fire():
            return

        idx = random.randint(0, len(comments)-1)
        data = comments[idx]
        self.client.post(self.tweet_endpoint, {"content": data})

    @task(VISIT_RATE_TIMELINE)
    def timeline(self):
        if not time_to_fire():
            return

        self.client.get(self.timeline_endpoint)

    @task(VISIT_RATE_NEWSFEED)
    def newsfeed(self):
        if not time_to_fire():
            return

        self.client.get(self.newsfeed_endpoint)

    @task(VISIT_RATE_FOLLOW)
    def follows(self):
        if not time_to_fire():
            return

        to_id = random.randint(1, MAX_TWITTER_USER_ID)
        if to_id == self.user_id:
            to_id = random.randint(1, MAX_TWITTER_USER_ID)

        self.client.post(self.follows_endpoint, {"id_to_follow": to_id})


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = NEXT_REQUEST_MIN_WAIT_MS
    max_wait = NEXT_REQUEST_MAX_WAIT_MS
