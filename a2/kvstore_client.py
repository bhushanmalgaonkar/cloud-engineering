#!/usr/bin/python3

import os
import sys
import grpc

import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_HOST, KV_STORE_PORT, KV_STORE_DB_PATH
from database_handler import DataBaseHandler
from util import generateId, file_iterator

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
            print('got chunk: ', chunk)
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

    '''
        Stores all the files in the directory in the key-value store
    '''
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

    '''
        Private function that downloads a file
    '''
    def __downloadfile(self, dir_id, doc_id, root, stub):
        print(type(dir_id), type(doc_id))
        save_path = os.path.join(root, doc_id)
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
    def download_file(self, dir_id, doc_id, root, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__downloadfile(dir_id, doc_id, root, stub)
        else:
            self.__downloadfile(dir_id, doc_id, root, stub)

    '''
        Saves all the files associated with dir_id at save_path
    '''
    def download_directory(self, dir_id, save_path):
        with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
            stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

            docs = self.db.get_doc_metadata(dir_id)
            for doc_id in docs:
                self.__downloadfile(dir_id, doc_id[0], save_path, stub)

    '''
        Returns all the chunks associated with given dir_id and optionally doc_id
    '''
    def get_chunk_metadata(self, dir_id, doc_id=None):
        return self.db.get_chunk_metadata(dir_id, doc_id)


if __name__ == "__main__":
    k = KeyValueStoreClient()
    dir_id = k.upload_directory(sys.argv[1])
    print('saving')
    k.download_directory(dir_id, 'proto-copy')