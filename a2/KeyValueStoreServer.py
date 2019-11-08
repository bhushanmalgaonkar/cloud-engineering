#!/usr/bin/python3

import os
import time
import threading
import sqlalchemy as db
from sqlalchemy.pool import QueuePool
from datetime import datetime

import grpc
from concurrent import futures
from uuid import uuid4

import kvstore_pb2, kvstore_pb2_grpc
from Constants import *

DB_PATH = 'kvstore.db'
ROOT_DIR = 'chunks'

class DataBaseHandler:
    def __init__(self, path):
        self.engine = db.create_engine('sqlite:///{}'.format(path))

        conn = self.engine.connect()        
        conn.execute(""" CREATE TABLE IF NOT EXISTS chunks (
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
        conn.execute(""" CREATE TABLE IF NOT EXISTS executions (
                        exec_id text NOT NULL,
                        exec_type text NOT NULL,
                        chunk_id text NOT NULL,
                        status text NOT NULL,
                        result_id text
                    ); """)

        '''
            stores execution status and result of entire map-reduce job
        '''
        conn.execute(""" CREATE TABLE IF NOT EXISTS jobs (
                        exec_id text NOT NULL,
                        code_id text NOT NULL,
                        dir_id text NOT NULL,
                        status text NOT NULL,
                        result_id text NOT NULL
                    ); """)

        # metadata = db.MetaData()
        # self.chunks_table = db.Table('chunks', metadata, autoload=True, autoload_with=engine)
        # self.executions_table = db.Table('executions', metadata, autoload=True, autoload_with=engine)
        # self.jobs_table = db.Table('jobs', metadata, autoload=True, autoload_with=engine)

    def execute(self, sql, params):
        conn = self.engine.connect()
        trans = conn.begin()
        try:
            conn.execute(sql, params)
            trans.commit()
        except:
            trans.rollback()
        conn.close()

    def execute_and_return(self, sql, params):
        conn = self.engine.connect()
        rs = conn.execute(sql, params)
        conn.close()
        return rs

class Listener(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, *args, **kwargs):
        self.db = DataBaseHandler(DB_PATH)
        if not os.path.exists(ROOT_DIR):
            os.makedirs(ROOT_DIR)

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
        return kvstore_pb2.Id(id = self.getBlockName())

    '''
        Saves the block of data on disk and updates table 'chunks' to keep track
    '''
    def UploadFile(self, data_block_itr, context):
        print('in upload', threading.get_ident())
        try:
            chunk_index = 0
            for data_block in data_block_itr:
                blockfilename = os.path.join(ROOT_DIR, self.getBlockName())
                with open(blockfilename, 'a') as f:
                    f.write(data_block.data)

                self.db.execute(""" INSERT INTO chunks (dir_id, doc_id, chunk_index, chunk_id)
                                VALUES (?, ?, ?, ?) """, \
                                (data_block.dir_id, data_block.doc_id, chunk_index, blockfilename))
                chunk_index += 1
            return kvstore_pb2.UploadStatus(status = 'success')
        except:
            return kvstore_pb2.UploadStatus(status = 'failed')

    def Download(self, id, context):
        # c = self.db.cursor()
        # c.execute(""" SELECT dir_id, doc_id, chunk_index, chunk_id 
        #                 FROM chunks
        #                 WHERE dir_id = ?
        #                 ORDER BY doc_id, chunk_index """, \
        #                     (id.id))
        # for row in c:
        #     print('select query result: ', row)
        pass

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