#!/usr/bin/python3

import os
import sys
import grpc
from datetime import datetime
from uuid import uuid4

import kvstore_pb2, kvstore_pb2_grpc
from Constants import *
from DataBaseHandler import DataBaseHandler

DB_PATH = 'kvstore.db'

'''
    Creates and returns random id that is very unlikely to occur twice
'''
def generateId():
    return '{}-{}'.format(uuid4(), datetime.now().strftime("%y%m%d-%H%M%S"))

'''
    Reads a file as text and returns an iterator of chunks each of size close to BLOCK_SIZE
'''
def file_iterator(filepath):
    # minimize rpc calls by send multiple lines in single rpc call
    # limit the total size of data < BLOCK_SIZE
    chunk_index = 0
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
                yield (chunk_index, '\n'.join(block))
                block.clear()
                block_size = 0
                chunk_index += 1
        
        if block_size > 0:
                yield (chunk_index, '\n'.join(block))

class KeyValueStoreClient:
    def __init__(self):
        self.db = DataBaseHandler(DB_PATH)

    def close(self, channel):
        channel.close()

    def upload_file(self, dir_id, filepath, stub):
        for chunk_index, chunk in file_iterator(filepath):
            # create unique chunk_id
            chunk_id = generateId()
            data_block = kvstore_pb2.DataBlock(key=chunk_id, value=chunk)

            for _ in range(3):
                save_status = stub.Save(data_block)
                if save_status.status == 'success':
                    break

            # save to database
            self.db.save_chunk(dir_id, filepath, chunk_index, chunk_id)
            print('saved {} {} {} {}'.format(dir_id, filepath, chunk_index, chunk_id))


    def upload_directory(self, dirpath):
        # create an id to keep all files in the directory together on the server
        # all the files can be accessed using this id
        dir_id = generateId()
        print('dir_id: {}'.format(dir_id))
        
        with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
            stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
            
            # recursively upload all the files in the given directory
            for r, d, f in os.walk(dirpath):
                for file in f:
                    filepath = os.path.join(r, file)
                    self.upload_file(dir_id, filepath, stub)
                
            channel.unsubscribe(self.close)

        return dir_id

    def get_chunk_metadata(self, dir_id, doc_id=None):
        ch = self.db.get_chunk_metadata(dir_id, doc_id)
        print(ch)

if __name__ == "__main__":
    k = KeyValueStoreClient()
    dir_id = k.upload_directory(sys.argv[1])
    k.get_chunk_metadata(dir_id)