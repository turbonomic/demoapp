from __future__ import print_function
import user_service_pb2
import user_service_pb2_grpc
import grpc

import logging
import os

USER_SERVICE_HOST = os.getenv('TWITTER_CASS_USER_SERVICE_HOST', 'localhost')
USER_SERVICE_PORT = os.getenv('TWITTER_CASS_USER_SERVICE_PORT', '50051')
CHANNEL_ADDR = '{}:{}'.format(USER_SERVICE_HOST, USER_SERVICE_PORT)


class UserService:
    def __init__(self):
        self.channel = grpc.insecure_channel(CHANNEL_ADDR)
        self.stub = user_service_pb2_grpc.TwitterUserStub(self.channel)
        logging.info("[user-service-grpc-client] Connected to grpc server at %s", CHANNEL_ADDR)

    def __del__(self):
        self.channel.close()

    def name(self, user_id):
        user = self.stub.GetUser(user_service_pb2.GetUserRequest(user_id=user_id))
        return user.name

    def names(self, user_ids):
        request = user_service_pb2.GetUsersRequest()
        request.user_ids[:] = user_ids
        users = self.stub.GetUsers(request)
        return users.names

    def check_session(self, user_id, session_key):
        res = self.stub.CheckSession(user_service_pb2.CheckSessionRequest(user_id=user_id, session_key=session_key))
        return res.ok

    def remove_session(self, session_key):
        res = self.stub.RemoveSession(user_service_pb2.RemoveSessionRequest(session_key=session_key))
        return res.ok

    def check_password(self, user_id, password):
        res = self.stub.CheckPassword(user_service_pb2.CheckPasswordRequest(user_id=user_id, password=password))
        return res.ok, res.session_key


user_svc = UserService()
