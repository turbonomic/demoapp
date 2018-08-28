import os
import logging
import tweet_service_pb2
import tweet_service_pb2_grpc
import grpc


TWEET_SERVICE_HOST = os.getenv('TWEET_SERVICE_HOST', 'localhost:50052')


class TweetService:
    def __init__(self):
        self.channel = grpc.insecure_channel(TWEET_SERVICE_HOST)
        self.stub = tweet_service_pb2_grpc.TweetStub(self.channel)
        logging.info("[tweet-service-grpc-client] Connected to grpc server at %s", TWEET_SERVICE_HOST)

    def __del__(self):
        self.channel.close()

    def tweet(self, user_id, content):
        logging.info("%d tweets %s" % (user_id, content))
        res = self.stub.Tweet(tweet_service_pb2.TweetRequest(user_id=user_id, content=content))
        return res.tweet_id

    def timeline(self, user_id, followees):
        logging.info("User %d follows %d people" % (user_id, len(followees)))
        tr = tweet_service_pb2.TimelineRequest(user_id=user_id)
        tr.followees[:] = followees
        # TODO: implement streaming
        timeline = list(self.stub.Timeline(tr))

        logging.info("%d tweets retrieved for timeline of user %d" % (len(timeline), user_id))

        return [{
                    'created_at': str(row.created_at),
                    'user_id': str(row.user_id),
                    'content': str(row.content),
                } for row in timeline]

    def news_feed(self, user_id):
        # TODO: implement streaming
        nfrequest = tweet_service_pb2.NewsfeedRequest(user_id=user_id)
        tweets = self.stub.Newsfeed(nfrequest)
        tweets = list(tweets)
        logging.info("%d tweets retrieved from user %d" % (len(tweets), user_id))
        return [{
                    'created_at': str(row.created_at),
                    'content': str(row.content),
                } for row in tweets]

tweet_svc = TweetService()
