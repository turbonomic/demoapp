import json
import os
import logging
import tweet_service_pb2
import tweet_service_pb2_grpc
import grpc
from retrying import retry

TWEET_SERVICE_HOST = os.getenv('TWITTER_CASS_TWEET_SERVICE_HOST', 'localhost')
TWEET_SERVICE_PORT = os.getenv('TWITTER_CASS_TWEET_SERVICE_PORT', '50052')
CHANNEL_ADDR = '{}:{}'.format(TWEET_SERVICE_HOST, TWEET_SERVICE_PORT)


class TweetService:
    def __init__(self):
        self.channel = grpc.insecure_channel(CHANNEL_ADDR)
        self.stub = tweet_service_pb2_grpc.TweetStub(self.channel)

    def __del__(self):
        self.channel.close()

    @retry(wait_fixed=100, stop_max_attempt_number=5)
    def tweet(self, user_id, content):
        logging.debug("%d tweets %s" % (user_id, content))
        res = self.stub.Tweet(tweet_service_pb2.TweetRequest(user_id=user_id, content=content))
        return res.tweet_id

    @retry(wait_fixed=100, stop_max_attempt_number=5)
    def timeline(self, user_id, followees):
        logging.debug("User %d follows %d people" % (user_id, len(followees)))
        tr = tweet_service_pb2.TimelineRequest(user_id=user_id)
        tr.followees[:] = followees
        # TODO: implement streaming
        timeline = list(self.stub.Timeline(tr))

        logging.debug("%d tweets retrieved for timeline of user %d" % (len(timeline), user_id))

        return [{
                    'created_at': row.created_at.encode('utf-8'),
                    'user_id': str(row.user_id),
                    'content': row.content.encode('utf-8'),
                } for row in timeline]

    @retry(wait_fixed=100, stop_max_attempt_number=5)
    def news_feed(self, user_id):
        # TODO: implement streaming
        nfrequest = tweet_service_pb2.NewsfeedRequest(user_id=user_id)
        tweets = self.stub.Newsfeed(nfrequest)
        tweets = list(tweets)
        logging.debug("%d tweets retrieved from user %d" % (len(tweets), user_id))
        return [{
                    'created_at': row.created_at.encode('utf-8'),
                    'content': row.content.encode('utf-8'),
                } for row in tweets]


tweet_svc = TweetService()
