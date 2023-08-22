import logging
import os
import random
import time

from locust import HttpUser, between, task

MAX_TWITTER_USER_ID = int(os.getenv("MAX_TWITTER_USER_ID", 101))
MAX_NUM_FOLLOWS = int(os.getenv("MAX_NUM_FOLLOWS", 50))
VISIT_RATE_TWEET = int(os.getenv("VISIT_RATE_TWEET", 1000))
VISIT_RATE_TIMELINE = int(os.getenv("VISIT_RATE_TIMELINE", 100))
VISIT_RATE_NEWSFEED = int(os.getenv("VISIT_RATE_NEWSFEED", 1000))
VISIT_RATE_FOLLOW = int(os.getenv("VISIT_RATE_FOLLOW", 10))
NEXT_REQUEST_MIN_WAIT_SECS = int(os.getenv("NEXT_REQUEST_MIN_WAIT_SECS", 1))
NEXT_REQUEST_MAX_WAIT_SECS = int(os.getenv("NEXT_REQUEST_MAX_WAIT_SECS", 10))

logging.info(f"MAX_TWITTER_USER_ID={MAX_TWITTER_USER_ID}")
logging.info(f"MAX_NUM_FOLLOWS={MAX_NUM_FOLLOWS}")
logging.info(f"VISIT_RATE_TWEET={VISIT_RATE_TWEET}")
logging.info(f"VISIT_RATE_TIMELINE={VISIT_RATE_TIMELINE}")
logging.info(f"VISIT_RATE_NEWSFEED={VISIT_RATE_NEWSFEED}")
logging.info(f"VISIT_RATE_FOLLOW={VISIT_RATE_FOLLOW}")
logging.info(f"NEXT_REQUEST_MIN_WAIT_SECS={NEXT_REQUEST_MIN_WAIT_SECS}")
logging.info(f"NEXT_REQUEST_MAX_WAIT_SECS={NEXT_REQUEST_MAX_WAIT_SECS}")


# TIME_SLOT_PROBABILITY is used to simulate varied workload, where for each time slot,
# the probability that a user will fire a request is the probability specified in the time slot.
# Examples: hourly pattern with 10-minute step: TIME_SLOT_PROBABILITY = '1.0,0.7,0.4,0.1,0.4,
# 0.7' TIME_SLOT_PROBABILITY_STEP_IN_MIN = '10'
#
#   6-hour pattern with one-hour step:  TIME_SLOT_PROBABILITY = '1.0,0.7,0.4,0.1,0.4,0.7'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '60'
#
#   daily pattern with 12-hour step:    TIME_SLOT_PROBABILITY = '1.0,0'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '720'
#
#   weekly pattern with one-day step:   TIME_SLOT_PROBABILITY = '1.0,0.9,0.9,0.9,0.8,0.3,0.2'
#                                       TIME_SLOT_PROBABILITY_STEP_IN_MIN = '1440'
ENABLE_TIME_SLOT_PROBABILITY = os.getenv("ENABLE_TIME_SLOT_PROBABILITY", "0") != "0"
TIME_SLOT_PROBABILITY = list(
    map(
        lambda p: int(100 * float(p)),
        os.getenv("TIME_SLOT_PROBABILITY", "1.0,0.7,0.4,0.1,0.4,0.7").split(","),
    )
)
TIME_SLOT_PROBABILITY_STEP_IN_MIN = int(
    os.getenv("TIME_SLOT_PROBABILITY_STEP_IN_MIN", "60")
)
TIME_SLOT_CYCLE_IN_MIN = len(TIME_SLOT_PROBABILITY) * TIME_SLOT_PROBABILITY_STEP_IN_MIN


def time_to_fire():
    if not ENABLE_TIME_SLOT_PROBABILITY:
        return True
    t = time.localtime()
    m = (
        ((t.tm_wday * 24 + t.tm_hour) * 60 + t.tm_min)
        % TIME_SLOT_CYCLE_IN_MIN
        // TIME_SLOT_PROBABILITY_STEP_IN_MIN
    )
    p = TIME_SLOT_PROBABILITY[m]
    return p >= random.randint(1, 100)


def read_comments():
    filename = os.getenv("TWEET_CONTENT_FILE", "/home/locust/comments.txt")
    with open(filename) as comments_file:
        comments = [line.rstrip() for line in comments_file]
    return comments


class TwitterUser(HttpUser):
    wait_time = between(NEXT_REQUEST_MIN_WAIT_SECS, NEXT_REQUEST_MAX_WAIT_SECS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = str(random.randint(1, MAX_TWITTER_USER_ID))
        self.password = self.user_id
        self.comments = read_comments()
        self.tweet_endpoint = "/tweet"
        self.timeline_endpoint = "/timeline"
        self.newsfeed_endpoint = "/newsfeed"
        self.follows_endpoint = "/follows"

    def on_start(self):
        self.user_id = self.client.post(
            "/setcookie", {"username": self.user_id, "password": self.password}
        )

    @task(VISIT_RATE_TWEET)
    def tweet(self):
        if not time_to_fire():
            return
        index = random.randint(0, len(self.comments) - 1)
        content = self.comments[index]
        self.client.post(self.tweet_endpoint, {"content": content})

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
        id_to_follow = random.randint(1, MAX_TWITTER_USER_ID)
        while id_to_follow == self.user_id:
            id_to_follow = random.randint(1, MAX_TWITTER_USER_ID)
        self.client.post(self.follows_endpoint, {"id_to_follow": id_to_follow})
