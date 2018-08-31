from concurrent import futures
import time
import logging
import friend_service_pb2
import friend_service_pb2_grpc
import grpc
from friend_service import friend_svc

GRPC_PORT = 50053


class FriendServicer(friend_service_pb2_grpc.FriendServicer):
    def Followees(self, request, context):
        user_id = request.user_id
        followees = friend_svc.followees(user_id=user_id)
        res = friend_service_pb2.FolloweesResponse()
        res.followees[:] = followees
        return res

    def Follows(self, request, context):
        user_id = request.user_id
        followee = request.followee
        done = friend_svc.follows(user_id, followee)
        return friend_service_pb2.FollowsResponse(done=done)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    friend_service_pb2_grpc.add_FriendServicer_to_server(
        FriendServicer(), server)
    server.add_insecure_port('[::]:' + str(GRPC_PORT))
    server.start()
    logging.info("GRPC server for friend service started")

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