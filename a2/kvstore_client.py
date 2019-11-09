#!/usr/bin/python3

import os
import sys
import grpc

import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_HOST, KV_STORE_PORT, KV_STORE_DB_PATH
from database_handler import DataBaseHandler
from util import generateId, file_iterator, str_iterator

class KeyValueStoreClient:
    def __init__(self):
        self.db = DataBaseHandler(KV_STORE_DB_PATH)

    def close(self, channel):
        channel.close()

    '''
        Private function that uploads a file.
    '''
    def __uploadfile(self, dir_id, filepath, stub):
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
            print('kvstore: saved {} {} {} {}'.format(dir_id, filepath, chunk_index, chunk_id))

    '''
        Adds a file to existing directory
    '''
    def upload_file(self, dir_id, filepath, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadfile(dir_id, filepath, stub)
        else:
            self.__uploadfile(dir_id, filepath, stub)

    def __uploadfilestr(self, dir_id, doc_id, string, stub):
        for chunk_index, chunk in str_iterator(string):
            # create unique chunk_id
            chunk_id = generateId()
            data_block = kvstore_pb2.DataBlock(key=chunk_id, value=chunk)

            for _ in range(3):
                save_status = stub.Save(data_block)
                if save_status.status == 'success':
                    break

            # save to database
            self.db.save_chunk(dir_id, doc_id, chunk_index, chunk_id)
            print('kvstore: saved {} {} {} {}'.format(dir_id, doc_id, chunk_index, chunk_id))

    def upload_file_str(self, dir_id, doc_id, string, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadfilestr(dir_id, doc_id, string, stub)
        else:
            self.__uploadfilestr(dir_id, doc_id, string, stub)

    '''
        Stores all the files in the directory in the key-value store
    '''
    def upload_directory(self, dirpath):
        # create an id to keep all files in the directory together on the server
        # all the files can be accessed using this id
        dir_id = generateId()
        print('kvstore: dir_id: {}'.format(dir_id))
        
        with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
            stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
            
            # recursively upload all the files in the given directory
            for r, d, f in os.walk(dirpath):
                for file in f:
                    filepath = os.path.join(r, file)
                    self.upload_file(dir_id, filepath, stub)
                
            channel.unsubscribe(self.close)

        return dir_id

    '''
        Private function that downloads a file
    '''
    def __downloadfile(self, dir_id, doc_id, root, flatten, stub):
        save_path = os.path.join(root, os.path.basename(doc_id) if flatten else doc_id)
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        
        with open(save_path, 'w') as f:
            chunks = self.get_chunk_metadata(dir_id, doc_id)
            for chunk in chunks:
                data = stub.Get(kvstore_pb2.Id(id = chunk[3])).value
                f.write(data)

    '''
        Downloads single file from key-value store
    '''
    def download_file(self, dir_id, doc_id, root, flatten=False, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__downloadfile(dir_id, doc_id, root, flatten, stub)
        else:
            self.__downloadfile(dir_id, doc_id, root, flatten, stub)

    '''
        Saves all the files associated with dir_id at save_path
    '''
    def download_directory(self, dir_id, save_path, flatten=False):
        with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
            stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

            docs = self.get_doc_metadata(dir_id)
            for doc_id in docs:
                self.download_file(dir_id, doc_id[0], save_path, flatten, stub)

    '''
        Reads and returns chunk content as a string
    '''
    def read_chunk(self, chunk_id):
        with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
            stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
            data = stub.Get(kvstore_pb2.Id(id = chunk_id)).value
            return data

    '''
        Downloads a chunk given chunk_id and saves it as file save_path
    '''
    def download_chunk(self, chunk_id, save_path):
        data = self.read_chunk(chunk_id)
        if data:
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path))
            
            with open(save_path, 'w') as f:
                f.write(data)
        
    '''
        Returns all unique doc_ids associated with directory 
    '''
    def get_doc_metadata(self, dir_id):
        return self.db.get_doc_metadata(dir_id)

    '''
        Returns all the chunks associated with given dir_id and optionally doc_id
    '''
    def get_chunk_metadata(self, dir_id, doc_id=None):
        return self.db.get_chunk_metadata(dir_id, doc_id)


if __name__ == "__main__":
    k = KeyValueStoreClient()
    dir_id = k.upload_directory(sys.argv[1])
    k.download_directory(dir_id, 'save_path', flatten=True)