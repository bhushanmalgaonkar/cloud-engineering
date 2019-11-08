#!/usr/bin/python3

import threading
from queue import Queue # thread safe
import time
import sys
import grpc
import asynctest_pb2, asynctest_pb2_grpc

mappers = Queue()

def close(channel):
    channel.close()

def sendRequest(host, port, data):
    global mappers

    with grpc.insecure_channel("{}:{}".format(host, port)) as channel:
        stub = asynctest_pb2_grpc.HelloWorldStub(channel)
        response = stub.sayHello(asynctest_pb2.HelloRequest(data = data))
        print("for {} received {}".format(data, response.status))
        channel.unsubscribe(close)
    
    print('adding back {}:{}'.format(host, port))
    mappers.put((host, port))

def run_client():
    global mappers
    for mp in [('localhost', 12345), ('localhost', 12346)]:
        mappers.put(mp)

    data = ['hi', 'hello', 'nice', 'wow']
    threads = []
    for d in data:
        while True:
            if mappers.empty():
                print('all mappers busy. wait...')
                time.sleep(2)
                continue
            else:
                break

        host, port = mappers.get()
        print('{}:{} is free, sending {}'.format(host, port, d))
        t = threading.Thread(target=sendRequest, args=(host, port, d, ), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    print('exiting')
    
if __name__ == "__main__":
    run_client()