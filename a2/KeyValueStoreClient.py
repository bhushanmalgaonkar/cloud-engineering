#!/usr/bin/python3

import os
import grpc

import kvstore_pb2, kvstore_pb2_grpc
from Constants import *

def close(channel):
    channel.close()

def file_iterator(dir_id, filepath):
    # minimize rpc calls by send multiple lines in single rpc call
    # limit the total size of data < BLOCK_SIZE
    with open(filepath, 'r') as f:
        block = []
        block_size = 0
        while True:
            line = f.readline()
            if not line:
                break

            block.append(line)
            block_size += len(line)
            if block_size > BLOCK_SIZE:
                yield kvstore_pb2.DataBlock(dir_id = dir_id, doc_id = filepath, data = '\n'.join(block))
                block.clear()
                block_size = 0
        
        if block_size > 0:
                yield kvstore_pb2.DataBlock(dir_id = dir_id, doc_id = filepath, data = '\n'.join(block))

def upload_directory(path):
    with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
        stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

        # create an id to keep all files in the directory together on the server
        # all the files can be accessed using this id
        dir_id = stub.CreateDirectory(kvstore_pb2.Empty()).id

        # recursively upload all the files in the given directory
        for r, d, f in os.walk(path):
            for file in f:
                filepath = os.path.join(r, file)
                
                print('Uploading {}'.format(filepath))
                status = stub.Upload(file_iterator(dir_id, filepath))
                if status.status == 'success':
                    break

        channel.unsubscribe(close)    

if __name__ == "__main__":
    run_client()