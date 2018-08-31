from concurrent import futures
import time
import logging
import user_service_pb2
import user_service_pb2_grpc
import grpc
from user_service import user_svc

GRPC_PORT = 50051


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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_TwitterUserServicer_to_server(
        UserServicer(), server)
    server.add_insecure_port('[::]:' + str(GRPC_PORT))
    server.start()
    logging.info("GRPC server for user service started")

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