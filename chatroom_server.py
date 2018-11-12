from concurrent import futures
import time
import random
import queue

import grpc

import chatroom_pb2
import chatroom_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

chatroomUsers = {}
chatroomNames = set()
queues = []

class ChatroomServicer(chatroom_pb2_grpc.ChatroomServicer):
    def Register(self, request, context):
        cname = request.name
        if cname is None or len(cname) >= 32:
            return chatroom_pb2.GeneralResponse(ok=False, msg='Illegal name')
        if cname in chatroomNames:
            return chatroom_pb2.GeneralResponse(ok=False, msg='This name has been used')

        token = ChatroomServicer._generateUserToken()
        chatroomNames.add(cname)
        chatroomUsers[token] = {
            'name': cname
        }
        self._putToQueues({
            'type': chatroom_pb2.Broadcast.USER_JOIN,
            'name': cname
        })

        print('User [{}] registered.'.format(cname))
        return chatroom_pb2.GeneralResponse(ok=True, msg='OK', token=token)

    def Chat(self, request, context):
        if not self._isAuthorized(request):
            return chatroom_pb2.GeneralResponse(ok=False, msg='Not authorized')
        if len(request.msg.strip()) == 0:
            return chatroom_pb2.GeneralResponse(ok=False, msg='Empty message')

        curUser = chatroomUsers[request.token]
        self._putToQueues({
            'type': chatroom_pb2.Broadcast.USER_MSG,
            'name': curUser['name'],
            'msg': request.msg
        })
        return chatroom_pb2.GeneralResponse(ok=True, msg='Sent')

    def Subscribe(self, request, context):
        if not self._isAuthorized(request):
            return chatroom_pb2.Broadcast()

        if 'stream' in chatroomUsers[request.token]:
            return chatroom_pb2.Broadcast(type=chatroom_pb2.Broadcast.FAILURE, msg='Already subscribed')

        q = queue.Queue()
        queues.append(q)
        chatroomUsers[request.token]['stream'] = q
        yield chatroom_pb2.Broadcast(type=chatroom_pb2.Broadcast.UNSPECIFIED)

        while True:
            q = chatroomUsers[request.token]['stream']
            obj = q.get()
            if obj is None:
                yield chatroom_pb2.Broadcast(type=chatroom_pb2.Broadcast.FAILURE, msg='The server is shutting down')
                return
            yield chatroom_pb2.Broadcast(**obj)
            q.task_done()

    def _putToQueues(self, obj):
        for token, user in chatroomUsers.items():
            if 'stream' in user:
                user['stream'].put(obj)

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
