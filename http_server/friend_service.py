from __future__ import print_function
import friend_service_pb2
import friend_service_pb2_grpc
import grpc
from retrying import retry
import logging
import os

FRIEND_SERVICE_HOST = os.getenv('TWITTER_CASS_FRIEND_SERVICE_HOST', 'localhost')
FRIEND_SERVICE_PORT = os.getenv('TWITTER_CASS_FRIEND_SERVICE_PORT', '50053')
CHANNEL_ADDR = '{}:{}'.format(FRIEND_SERVICE_HOST, FRIEND_SERVICE_PORT)


class FriendService:
    def __init__(self):
        self.channel = grpc.insecure_channel(CHANNEL_ADDR)
        self.stub = friend_service_pb2_grpc.FriendStub(self.channel)
        logging.info("[friend-service-grpc-client] Connected to grpc server at %s", CHANNEL_ADDR)

    def __del__(self):
        self.channel.close()

    @retry(wait_fixed=100, stop_max_attempt_number=5)
    def followees(self, user_id):
        res = self.stub.Followees(friend_service_pb2.FolloweesRequest(user_id=user_id))
        return list(res.followees)

    def followers(self, user_id):
        pass

    @retry(wait_fixed=100, stop_max_attempt_number=5)
    def follows(self, from_id, to_id):
        res = self.stub.Follows(friend_service_pb2.FollowsRequest(user_id=from_id, followee=to_id))
        return res.done

    def count_follows(self, user_id):
        pass


friend_svc = FriendService()
