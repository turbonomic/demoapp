import instana
import logging
from os import path
import sys
import time
import user_service_pb2
import user_service_pb2_grpc
from user_service import UserService
sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'common_service'))
from common_service import create_grpc_server  # noqa: E402

GRPC_PORT = 50051

user_svc = UserService()


class UserServicer(user_service_pb2_grpc.TwitterUserServicer):

    def GetUser(self, request, context):
        user_id = request.user_id
        name = user_svc.get_name(user_id)
        return user_service_pb2.GetUserResponse(user_id=user_id, name=name)

    def GetUsers(self, request, context):
        names = user_svc.get_names(list(request.user_ids))
        res = user_service_pb2.GetUsersResponse()
        res.names[:] = names
        return res

    def CheckPassword(self, request, context):
        user_id = request.user_id
        password = request.password
        ok, session_key = user_svc.check_password(user_id, password)
        return user_service_pb2.CheckPasswordResponse(ok=ok, session_key=session_key)

    def CheckSession(self, request, context):
        user_id = request.user_id
        session_key = request.session_key
        ok = user_svc.check_session(user_id, session_key)
        return user_service_pb2.CheckSessionResponse(ok=ok)

    def RemoveSession(self, request, context):
        session_key = request.session_key
        ok = user_svc.remove_session(session_key)
        return user_service_pb2.RemoveSessionResponse(ok=ok)


if __name__ == '__main__':
    server = create_grpc_server(GRPC_PORT)
    user_service_pb2_grpc.add_TwitterUserServicer_to_server(UserServicer(), server)
    server.start()

    logging.info("GRPC server for user service started")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)
