import os
from locust import HttpLocust, TaskSet, task
import random
import time
import logging

MAX_TWITTER_USER_ID = int(os.getenv('MAX_TWITTER_USER_ID', 101))
MAX_NUM_FOLLOWS = int(os.getenv('MAX_NUM_FOLLOWS', 50))
VISIT_RATE_TWEET = int(os.getenv('VISIT_RATE_TWEET', 0))
VISIT_RATE_TIMELINE = int(os.getenv('VISIT_RATE_TIMELINE', 0))
VISIT_RATE_NEWSFEED = int(os.getenv('VISIT_RATE_NEWSFEED', 100))
VISIT_RATE_FOLLOW = int(os.getenv('VISIT_RATE_FOLLOW', 0))
NEXT_REQUEST_MIN_WAIT_MS = int(os.getenv('NEXT_REQUEST_MIN_WAIT_MS', 1000))
NEXT_REQUEST_MAX_WAIT_MS = int(os.getenv('NEXT_REQUEST_MAX_WAIT_MS', 3000))

logging.info("\n\tMAX_TWITTER_USER_ID=%s\n\tMAX_NUM_FOLLOWS=%s\n\tVISIT_RATE_TWEET=%s\n\tVISIT_RATE_TIMELINE=%s"
             "\n\tVISIT_RATE_NEWSFEED=%s\n\tVISIT_RATE_FOLLOW=%s\n\tNEXT_REQUEST_MIN_WAIT_MS=%s\n\tNEXT_REQUEST_MAX_WAIT_MS=%s",
             MAX_TWITTER_USER_ID, MAX_NUM_FOLLOWS, VISIT_RATE_TWEET, VISIT_RATE_TIMELINE,
             VISIT_RATE_NEWSFEED, VISIT_RATE_FOLLOW, NEXT_REQUEST_MIN_WAIT_MS, NEXT_REQUEST_MAX_WAIT_MS)

# TIME_SLOT_PROBABILITY is used to simulate varied workload, where for each time slot, the probability that a user
# will fire a request is the probability specified in the time slot.
# Examples:
#   hourly pattern with 10-minute step: TIME_SLOT_PROBABILITY = '1.0,0.7,0.4,0.1,0.4,0.7'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '10'
#
#   6-hour pattern with one-hour step:  TIME_SLOT_PROBABILITY = '1.0,0.7,0.4,0.1,0.4,0.7'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '60'
#
#   daily pattern with 12-hour step:    TIME_SLOT_PROBABILITY = '1.0,0'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '720'
#
#   weekly pattern with one-day step:   TIME_SLOT_PROBABILITY = '1.0,0.9,0.9,0.9,0.8,0.3,0.2'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '1440'
ENABLE_TIME_SLOT_PROBABILITY = os.getenv('ENABLE_TIME_SLOT_PROBABILITY', '0') != '0'
TIME_SLOT_PROBABILITY = list(map(lambda p:int(100*float(p)), os.getenv('TIME_SLOT_PROBABILITY', '1.0,0.7,0.4,0.1,0.4,0.7').split(',')))
TIME_SLOT_PROBABILITY_STEP_IN_MIN = int(os.getenv('TIME_SLOT_PROBABILITY_STEP_IN_MIN', '60'))
TIME_SLOT_CYCLE_IN_MIN = len(TIME_SLOT_PROBABILITY) * TIME_SLOT_PROBABILITY_STEP_IN_MIN

if ENABLE_TIME_SLOT_PROBABILITY:
    logging.info("Varied workload with %s-minute cycle is enabled: prob = %s with step = %s minutes",
                 TIME_SLOT_CYCLE_IN_MIN, TIME_SLOT_PROBABILITY, TIME_SLOT_PROBABILITY_STEP_IN_MIN)

def time_to_fire():
    if not ENABLE_TIME_SLOT_PROBABILITY:
        return True

    t = time.localtime()
    m = ((t.tm_wday * 24 + t.tm_hour) * 60 + t.tm_min) % TIME_SLOT_CYCLE_IN_MIN // TIME_SLOT_PROBABILITY_STEP_IN_MIN

    p = TIME_SLOT_PROBABILITY[m]
    return p >= random.randint(1,100)

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
