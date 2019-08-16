"""
Author: Zhongying Wang
Email: kerbalwzy@gmail.com
DateTime: 2019-08-13T23:30:00Z
PythonVersion: Python3.6.3
"""
import os
import sys
import time
import grpc

from threading import Thread
from concurrent import futures

# add the `demo_grpc_dps` dir into python package search paths
BaseDir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BaseDir, "demo_grpc_pbs"))

from demo_grpc_pbs import demo_pb2, demo_pb2_grpc

SERVER_ADDRESS = 'localhost:23334'
SERVER_ID = 1


class DemoServer(demo_pb2_grpc.GRPCDemoServicer):

    # 简单模式
    # unary-unary
    def SimpleMethod(self, request, context):
        print("SimpleMethod called by client(%d) the message: %s" % (request.client_id, request.request_data))
        response = demo_pb2.Response(server_id=SERVER_ID, response_data="Python server SimpleMethod Ok!!!!")
        return response

    # 客户端流模式（在一次调用中, 客户端可以多次向服务器传输数据, 但是服务器只能返回一次响应）
    # stream-unary (In a single call, the client can transfer data to the server several times,
    # but the server can only return a response once.)
    def ClientStreamingMethod(self, request_iterator, context):
        print("ClientStreamingMethod called by client...")
        for request in request_iterator:
            print("recv from client(%d), message= %s" % (request.client_id, request.request_data))
        response = demo_pb2.Response(server_id=SERVER_ID, response_data="Python server ClientStreamingMethod ok")
        return response

    # 服务端流模式（在一次调用中, 客户端只能一次向服务器传输数据, 但是服务器可以多次返回响应）
    # unary-stream (In a single call, the client can only transmit data to the server at one time,
    # but the server can return the response many times.)
    def ServerStreamingMethod(self, request, context):
        print("ServerStreamingMethod called by client(%d), message= %s" % (request.client_id, request.request_data))

        # 创建一个生成器
        # create a generator
        def response_messages():
            for i in range(5):
                response = demo_pb2.Response(server_id=SERVER_ID, response_data=("send by Python server, message=%d" % i))
                yield response

        return response_messages()

    # 双向流模式 (在一次调用中, 客户端和服务器都可以向对方多次收发数据)
    # stream-stream (In a single call, both client and server can send and receive data
    # to each other multiple times.)
    def BidirectionalStreamingMethod(self, request_iterator, context):
        print("BidirectionalStreamingMethod called by client...")

        # 开启一个子线程去接收数据
        # Open a sub thread to receive data
        def parse_request():
            for request in request_iterator:
                print("recv from client(%d), message= %s" % (request.client_id, request.request_data))

        t = Thread(target=parse_request)
        t.start()

        for i in range(5):
            yield demo_pb2.Response(server_id=SERVER_ID, response_data=("send by Python server, message= %d" % i))

        t.join()


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    demo_pb2_grpc.add_GRPCDemoServicer_to_server(DemoServer(), server)

    server.add_insecure_port(SERVER_ADDRESS)
    print("------------------start Python GRPC server")
    server.start()

    # In python3, `server` have no attribute `wait_for_termination`
    while 1:
        time.sleep(10)


if __name__ == '__main__':
    main()
