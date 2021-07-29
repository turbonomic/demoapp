import instana
import threading
import time
import logging
import tweet_service_pb2
import tweet_service_pb2_grpc
import sys
from os import path
from tweet_service import TweetService
sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'common_service'))
from common_service import options, create_grpc_server  # noqa: E402

GRPC_PORT = 50052

tweet_svc = TweetService(threading.Lock())


class TweetServicer(tweet_service_pb2_grpc.TweetServicer):
    def Tweet(self, request, context):
        tweet_id = tweet_svc.tweet(request.user_id, request.content)
        return tweet_service_pb2.TweetResponse(tweet_id=tweet_id)

    def Timeline(self, request, context):
        # TODO: implement streaming
        timeline = tweet_svc.timeline(request.user_id, request.followees)
        for tweet in timeline:
            yield tweet_service_pb2.TimelineResponse(
                user_id=int(tweet['user_id']),
                content=tweet['content'],
                created_at=tweet['created_at'],
            )

    def Newsfeed(self, request, context):
        # TODO: implement streaming
        tweets = tweet_svc.news_feed(request.user_id)
        for tweet in tweets:
            yield tweet_service_pb2.NewsfeedResponse(
                content=tweet['content'],
                created_at=tweet['created_at'],
            )


if __name__ == '__main__':
    server = create_grpc_server(GRPC_PORT)
    tweet_service_pb2_grpc.add_TweetServicer_to_server(TweetServicer(), server)
    server.start()

    logging.info("GRPC server for tweet service started")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)
