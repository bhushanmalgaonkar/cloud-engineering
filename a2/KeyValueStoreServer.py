#!/usr/bin/python3

import time
import threading
import sqlite3
from datetime import datetime

import grpc
from concurrent import futures
from uuid import uuid4

import kvstore_pb2, kvstore_pb2_grpc
from Constants import *

DB_PATH = 'kvstore.db'

class Listener(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, *args, **kwargs):
        self.db = sqlite3.connect(DB_PATH)

        c = self.db.cursor()
        c.execute(""" CREATE TABLE IF NOT EXISTS chunks (
                        dir_id text NOT NULL,
                        doc_id text NOT NULL,
                        chunk_index int NOT NULL,
                        chunk_id text PRIMARY KEY
                    ); """)

        '''
            exec_type: map/reduce
            status: pending/success/failed

            stores execution status of individual mapper/reducer.
            it is updated by master when worker finishes. 
            used by master to 
                1. collect output of mappers to give to reducers
                2. collect output of reducer to answer user query
        '''
        c.execute(""" CREATE TABLE IF NOT EXISTS executions (
                        exec_id text NOT NULL,
                        exec_type text NOT NULL,
                        chunk_id text NOT NULL,
                        status text NOT NULL,
                        result_id text
                    ); """)

        '''
            stores execution status and result of entire map-reduce job
        '''
        c.execute(""" CREATE TABLE IF NOT EXISTS jobs (
                        exec_id text NOT NULL,
                        code_id text NOT NULL,
                        dir_id text NOT NULL,
                        status text NOT NULL,
                        result_id text NOT NULL
                    ); """)
        
    '''
        Creates and returns random id that is very unlikely to occur twice
    '''
    def getBlockName(self):
        return '{}-{}'.format(uuid4(), datetime.now().strftime("%y%m%d-%H%M%S"))

    '''
        Creates and returns unique id to represent a bunch of files.
        The client can send this id in upload requests to keep files together.
    '''
    def CreateDirectory(self, request, context):
        return self.getBlockName()

    '''
        Saves the block of data on disk and updates table 'chunks' to keep track
    '''
    def Upload(self, data_block_itr, context):
        chunk_index = 0
        for data_block in data_block_itr:
            blockfilename = self.getBlockName()
            with open(blockfilename, 'a') as f:
                f.write(data_block.data)

            c = self.db.cursor()
            c.execute(""" INSERT INTO chunks (dir_id, doc_id, chunk_index, chunk_id)
                            VALUES (?, ?, ?, ?) """, \
                            (data_block.dir_id, data_block.doc_id, chunk_index, blockfilename))
            chunk_index += 1

    def Download(self, id, context):
        

    # def get(self, file_id, context):
    #     filename = file_id.id
    #     if filename.endswith('-b'):
    #         with open(filename.strip('\n'), 'r') as f:
    #             for line in f:
    #                 yield kvstore_pb2.FileData(data = line)
    #     elif filename.endswith('-r'):
    #         with open(filename, 'r') as rf:
    #             for blockfile in rf:
    #                 with open(blockfile.strip('\n'), 'r') as f:
    #                     for line in f:  
    #                         yield kvstore_pb2.FileData(data = line)

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