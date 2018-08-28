from __future__ import print_function
import user_service_pb2
import user_service_pb2_grpc
import grpc

import logging
import os

USER_SERVICE_HOST = os.getenv('USER_SERVICE_HOST', 'localhost:50051')


class UserService:
    def __init__(self):
        self.channel = grpc.insecure_channel(USER_SERVICE_HOST)
        self.stub = user_service_pb2_grpc.TwitterUserStub(self.channel)
        logging.info("[user-service-grpc-client] Connected to grpc server at %s", USER_SERVICE_HOST)

    def __del__(self):
        self.channel.close()

    def name(self, user_id):
        user = self.stub.GetUser(user_service_pb2.GetUserRequest(user_id=user_id))
        return user.name

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
