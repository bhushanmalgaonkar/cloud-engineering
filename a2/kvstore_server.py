#!/usr/bin/python3

import os
import time
import threading
import logging as log
from datetime import datetime

import grpc
from concurrent import futures
from uuid import uuid4

import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_ROOT_DIR, KV_STORE_PORT, KV_STORE_BLOCK_SIZE

class Listener(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, *args, **kwargs):
        try:
            if not os.path.exists(KV_STORE_ROOT_DIR):
                os.makedirs(KV_STORE_ROOT_DIR)
        except:
            log.error('Error creating base directory \'{}\'.'.format(KV_STORE_ROOT_DIR))
            exit(1)

    def Save(self, data_block, context):
        log.info('Save:{}'.format(data_block.key))
        try:
            blockfilename = os.path.join(KV_STORE_ROOT_DIR, data_block.key)
            with open(blockfilename, 'wb') as f:
                f.write(data_block.value)
            return kvstore_pb2.SaveStatus(status = 'success')
        except:
            return kvstore_pb2.SaveStatus(status = 'failed')

    def Get(self, id, context):
        log.debug('Get :{}'.format(id.id))
        try:
            blockfilename = os.path.join(KV_STORE_ROOT_DIR, id.id)
            data = bytes()
            with open(blockfilename, 'rb') as f:
                while True:
                    block = f.read(KV_STORE_BLOCK_SIZE)
                    if not block:
                        break
                    data += block
            return kvstore_pb2.DataBlock(key=id.id, value=data, error=False)
        except:
            return kvstore_pb2.DataBlock(key=id.id, value=bytes(), error=True)
            

def run_kvstore_server(port=KV_STORE_PORT):
    if not os.path.exists('logs') or not os.path.isdir('logs'):
        os.makedirs('logs')

    level = log.DEBUG
    log.basicConfig(format='%(levelname)s: %(message)s',
                        level=level, filename='logs/kvstore-{}.log'.format(port))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(Listener(), server)
    server.add_insecure_port("0.0.0.0:{}".format(port))
    server.start()
    log.info('KeyValueStore server listening on port {}'.format(port))
    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            log.error("KeyboardInterrupt on kvstore:{}".format(port))
            server.stop(0)
            break
        except:
            pass

if __name__ == "__main__":
    run_kvstore_server()