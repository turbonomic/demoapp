import os
from locust import HttpLocust, TaskSet, task
import random

MAX_TWITTER_USER_ID = os.getenv('MAX_TWITTER_USER_ID', 101)
MAX_NUM_FOLLOWS = os.getenv('MAX_NUM_FOLLOWS', 50)

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

    @task(1000)
    def tweet(self):
        idx = random.randint(0, len(comments)-1)
        data = comments[idx]
        self.client.post(self.tweet_endpoint, {"content": data})

    @task(100)
    def timeline(self):
        self.client.get(self.timeline_endpoint)

    @task(1000)
    def newsfeed(self):
        self.client.get(self.newsfeed_endpoint)

    @task(10)
    def follows(self):
        to_id = random.randint(1, MAX_TWITTER_USER_ID)
        if to_id == self.user_id:
            to_id = random.randint(1, MAX_TWITTER_USER_ID)

        self.client.post(self.follows_endpoint, {"id_to_follow": to_id})


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 10000
