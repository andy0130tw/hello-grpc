# hello-grpc
A naive chatroom featuring (!) gRPC, owo

[**See it in action!**](https://imgur.com/C6rZUYN)

# Building

Install dependencies:

```bash
pip3 install grpcio grpcio-tools googleapis-common-protos
```

You can refer to [this tutorial on gRPC](https://grpc.io/docs/quickstart/python.html).

To generate classes for services, run `python codegen.py`. This generates two python files. It should be noticed you may need to update `protobuf` if this step fails.

```bash
pip3 install protobuf --upgrade
```

# Running

Run the server first: `python chatroom_server.py`. The server will be up and will listen for clients on (hardcoded :)) port 50051.

You can then run several clients: `python chatroom_client.py` and try sending some messages.
