#!/usr/bin/python3

import os
import time
import threading
from datetime import datetime

import grpc
from concurrent import futures
from uuid import uuid4

import kvstore_pb2, kvstore_pb2_grpc
from Constants import *

ROOT_DIR = 'chunks'

class Listener(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, *args, **kwargs):
        try:
            if not os.path.exists(ROOT_DIR):
                os.makedirs(ROOT_DIR)
        except:
            print('Error creating base director \'chunks\'.')
            exit(1)

    def Save(self, data_block, context):
        try:
            blockfilename = os.path.join(ROOT_DIR, data_block.key)
            with open(blockfilename, 'w') as f:
                f.write(data_block.value)
            return kvstore_pb2.SaveStatus(status = 'success')
        except:
            return kvstore_pb2.SaveStatus(status = 'failed')

    def Get(self, id, context):
        try:
            blockfilename = os.path.join(ROOT_DIR, id.id)
            with open(blockfilename, 'r') as f:
                data = '\n'.join(f.readlines())
            return kvstore_pb2.DataBlock(key = id.id, value = data, error = False)
        except:
            return kvstore_pb2.DataBlock(key = id.id, value = 'NULL', error = True)
            

def run_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(Listener(), server)
    server.add_insecure_port("[::]:{}".format(KV_STORE_PORT))
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
    run_server()