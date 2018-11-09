import grpc
import threading
import queue

import chatroom_pb2
import chatroom_pb2_grpc

def add_input(input_queue, stub, token):
    while True:
        try:
            msg = input('Message: ')
            chatResp = stub.Chat(chatroom_pb2.ChatRequest(token=token, msg=msg))
        except EOFError:
            return

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chatroom_pb2_grpc.ChatroomStub(channel)

        name = input('Your name: ')
        registerResp = stub.Register(chatroom_pb2.RegisterRequest(name=name))
        if not registerResp.ok:
            print('Failed to register chatroom: {}'.format(registerResp.msg))
            return

        token = registerResp.token
        print('Token: {}'.format(token))

        subscribeResps = stub.Subscribe(chatroom_pb2.SubscribeRequest(token=token))
        subscribeResp = next(subscribeResps)
        if subscribeResp is None:
            print('Failed to subscribe chatroom')
            return
        print('Success')

        input_queue = queue.Queue()
        input_thread = threading.Thread(target=add_input, args=(input_queue, stub, token,))
        input_thread.daemon = True
        input_thread.start()

        for resp in subscribeResps:
            print('\x1b[1K\x1b[G> {}: {}'.format(resp.name, resp.msg))


if __name__ == '__main__':
    run()
