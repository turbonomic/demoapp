from concurrent import futures
import time
import logging
import tweet_service_pb2
import tweet_service_pb2_grpc
import grpc
from tweet_service import tweet_svc

GRPC_PORT = 50052


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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tweet_service_pb2_grpc.add_TweetServicer_to_server(
        TweetServicer(), server)
    server.add_insecure_port('[::]:' + str(GRPC_PORT))
    server.start()
    logging.info("GRPC server for tweet service started")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel('INFO')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(module)s] [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)

    serve()
