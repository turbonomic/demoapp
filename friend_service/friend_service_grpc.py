import instana
import time
import logging
from os import path
import sys
import friend_service_pb2
import friend_service_pb2_grpc
from friend_service import FriendService
sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'common_service'))
from common_service import create_grpc_server  # noqa: E402

GRPC_PORT = 50053

friend_svc = FriendService()


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


if __name__ == '__main__':
    server = create_grpc_server(GRPC_PORT)
    friend_service_pb2_grpc.add_FriendServicer_to_server(FriendServicer(), server)
    server.start()

    logging.info("GRPC server for friend service started")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)
