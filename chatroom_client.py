import grpc
import threading
import queue

import chatroom_pb2
import chatroom_pb2_grpc

def add_input(input_queue, stub, token):
    while True:
        try:
            msg = input('Message: ')
            if len(msg.strip()) == 0:
                continue
            chatResp = stub.Chat(chatroom_pb2.ChatRequest(token=token, msg=msg))
        except EOFError:
            return

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chatroom_pb2_grpc.ChatroomStub(channel)

        name = input('Your name: ')
        registerResp = stub.Register(chatroom_pb2.RegisterRequest(name=name))
        if not registerResp.ok:
            print('Failed to register chatroom: {}'.format(registerResp.msg))
            return

        token = registerResp.token

        subscribeResps = stub.Subscribe(chatroom_pb2.SubscribeRequest(token=token))
        subscribeResp = next(subscribeResps)
        if subscribeResp is None:
            print('Failed to subscribe chatroom')
            return
        print('Successfully joined the chatroom')

        input_queue = queue.Queue()
        input_thread = threading.Thread(target=add_input, args=(input_queue, stub, token))
        input_thread.daemon = True
        input_thread.start()

        for resp in subscribeResps:
            if resp.type == chatroom_pb2.Broadcast.USER_JOIN:
                print('\x1b[1K\x1b[G+ [{}] has joined the chat'.format(resp.name))
            elif resp.type == chatroom_pb2.Broadcast.USER_LEAVE:
                print('\x1b[1K\x1b[G- [{}] has left the chat'.format(resp.name))
            elif resp.type == chatroom_pb2.Broadcast.FAILURE:
                print('\x1b[1K\x1b[G!!! Failure: {}'.format(resp.msg))
                break
            elif resp.type == chatroom_pb2.Broadcast.UNSPECIFIED:
                continue
            else:
                print('\x1b[1K\x1b[G> {}: {}'.format(resp.name, resp.msg))


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Bye')
