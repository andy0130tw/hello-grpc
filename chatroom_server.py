from concurrent import futures
import time
import random
import queue

import grpc

import chatroom_pb2
import chatroom_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

chatroomUsers = {}
queues = []

class ChatroomServicer(chatroom_pb2_grpc.ChatroomServicer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def Register(self, request, context):
        if request.name is None or len(request.name) >= 32:
            return chatroom_pb2.GeneralResponse(ok=False, msg='Illegal name')
        token = ChatroomServicer._generateUserToken()
        chatroomUsers[token] = {
            'name': request.name,
            'stream': None
        }
        return chatroom_pb2.GeneralResponse(ok=True, msg='OK', token=token)

    def Chat(self, request, context):
        if not self._isAuthorized(request):
            return chatroom_pb2.GeneralResponse(ok=False, msg='Not authorized')

        curUser = chatroomUsers[request.token]
        self._putToQueues(request.token, { 'name': curUser['name'], 'msg': request.msg })
        return chatroom_pb2.GeneralResponse(ok=True, msg='Sent')

    def Subscribe(self, request, context):
        if not self._isAuthorized(request):
            return None

        q = queue.Queue()
        queues.append(q)
        chatroomUsers[request.token]['queue'] = q
        yield chatroom_pb2.Broadcast(type=0)

        while True:
            obj = chatroomUsers[request.token]['queue'].get()
            yield chatroom_pb2.Broadcast(type=2, **obj)

    def _putToQueues(self, user_token, obj):
        for token, user in chatroomUsers.items():
            if token == user_token:
                continue
            if 'queue' in user:
                user['queue'].put(obj)

    def _isAuthorized(self, request):
        return not(request.token is None or request.token not in chatroomUsers)

    @staticmethod
    def _generateUserToken():
        return random.getrandbits(64)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatroom_pb2_grpc.add_ChatroomServicer_to_server(ChatroomServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print('>>> Server started')
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        print('>>> Exiting')
        # to unblock all queues
        for q in queues:
            q.put(None)
        server.stop(0)


if __name__ == '__main__':
    serve()
