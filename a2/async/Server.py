#!/usr/bin/python3

from random import randint
from concurrent import futures
import time
import sys

import grpc
import asynctest_pb2, asynctest_pb2_grpc

class Listener(asynctest_pb2_grpc.HelloWorldServicer):
    def __init__(self, *args, **kwargs):
        pass

    def sayHello(self, request, context):
        print('received', request.data)
        sl = randint(1, 10)
        print("sleeping for {} seconds".format(sl))
        time.sleep(randint(1, 10))
        return asynctest_pb2.HelloResponse(status = 'success')


def run_server(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    asynctest_pb2_grpc.add_HelloWorldServicer_to_server(Listener(), server)
    server.add_insecure_port("[::]:{}".format(port))
    server.start()
    while True:
        try:
            print(f"active threads: {threading.active_count()}")
            time.sleep(5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            server.stop(0)
            break
        except:
            pass

if __name__ == "__main__":
    run_server(sys.argv[1])