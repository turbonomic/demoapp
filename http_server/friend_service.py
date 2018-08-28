from __future__ import print_function
import friend_service_pb2
import friend_service_pb2_grpc
import grpc

import logging
import os

FRIEND_SERVICE_HOST = os.getenv('FRIEND_SERVICE_HOST', 'localhost:50053')


class FriendService:
    def __init__(self):
        self.channel = grpc.insecure_channel(FRIEND_SERVICE_HOST)
        self.stub = friend_service_pb2_grpc.FriendStub(self.channel)
        logging.info("[friend-service-grpc-client] Connected to grpc server at %s", FRIEND_SERVICE_HOST)

    def __del__(self):
        self.channel.close()

    def followees(self, user_id):
        res = self.stub.Followees(friend_service_pb2.FolloweesRequest(user_id=user_id))
        return list(res.followees)

    def followers(self, user_id):
        pass

    def follows(self, from_id, to_id):
        res = self.stub.Follows(friend_service_pb2.FollowsRequest(user_id=from_id, followee=to_id))
        return res.done

    def count_follows(self, user_id):
        pass


friend_svc = FriendService()
