#!/usr/bin/python3

import os
import sys
import grpc
import pickle
import logging as log

import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_PORT, KV_STORE_ENCODING, KV_STORE_BLOCK_SIZE
from database_handler import DataBaseHandler
from util import generateId, file_iterator, str_iterator
from resource_manager import ResourceManager

class KeyValueStoreClient:
    def __init__(self, kvstore_host):
        log.info("Initializing KeyValueStoreClient")

        self.rm = ResourceManager()
        self.KV_STORE_HOST = kvstore_host
        self.KV_STORE_DB_PATH = 'mysql+pymysql://root:P@ssword123@{}:3306/kvstore'.format(kvstore_host)
        self.db = DataBaseHandler(self.KV_STORE_DB_PATH)

        log.info("Initializing KeyValueStoreClient is successful")

    '''
        Upload a bytes object as document
    '''
    def upload_bytes(self, dir_id, doc_id, bytez, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadbytes(dir_id, doc_id, bytez, stub)
                channel.unsubscribe(self.close)
        else:
            self.__uploadbytes(dir_id, doc_id, bytez, stub)

    '''
        Reads and returns the document as bytes() object
    '''
    def read_bytes(self, dir_id, doc_id, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                bytez = self.__readbytes(dir_id, doc_id, stub)
                channel.unsubscribe(self.close)
        else:
            bytez = self.__readbytes(dir_id, doc_id, stub)
        return bytez

    '''
        Reads a text file and saves it in key-value store
    '''
    def upload_file(self, dir_id, filepath, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadfile(dir_id, filepath, stub)
                channel.unsubscribe(self.close)
        else:
            self.__uploadfile(dir_id, filepath, stub)

    '''
        Upload a string as a document
    '''
    def upload_file_str(self, dir_id, doc_id, string, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadfilestr(dir_id, doc_id, string, stub)
                channel.unsubscribe(self.close)
        else:
            self.__uploadfilestr(dir_id, doc_id, string, stub)

    '''
        Upload an entire directory
    '''
    def upload_directory(self, dirpath, stub=None):
        log.info("Uploading directory {}".format(dirpath))
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                dir_id = self.__uploaddirectory(dirpath, stub)
                channel.unsubscribe(self.close)
        else:
            dir_id = self.__uploaddirectory(dirpath, stub)

        log.info("Uploading directory {} is successful. dir_id: {}".format(dirpath, dir_id))
        return dir_id 

    '''
        Saves all the files associated with dir_id at save_path
    '''
    def download_directory(self, dir_id, save_path, flatten=False, stub=None):
        log.info("Downloading directory {} at {}".format(dir_id, save_path))
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__downloaddirectory(dir_id, save_path, flatten, stub)
                channel.unsubscribe(self.close)
        else:
            self.__downloaddirectory(dir_id, save_path, flatten, stub)

        log.info("Downloading directory {} at {} is successful".format(dir_id, save_path))

    '''
        Downloads single file from key-value store
    '''
    def download_file(self, dir_id, doc_id, root, flatten=False, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__downloadfile(dir_id, doc_id, root, flatten, stub)
        else:
            self.__downloadfile(dir_id, doc_id, root, flatten, stub)

    '''
        Downloads a chunk given chunk_id and saves it as file save_path
    '''
    def download_chunk(self, chunk_id, save_path, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                data = self.__readchunk(chunk_id, stub)
        else:
            data = self.__readchunk(chunk_id, stub)

        if data:
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path))
            
            data = data.decode(KV_STORE_ENCODING)
            with open(save_path, 'w') as f:
                f.write(data)

    '''
        Reads and returns chunk content as a string
    '''
    def read_chunk(self, chunk_id, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(self.KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                return self.__readchunk(chunk_id, stub)
        else:
            return self.__readchunk(chunk_id, stub)
        
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


    ''' Private, helper methods '''

    '''
        Saves the block of bytes in key-values store and records it in the database
    '''
    def __uploadblock(self, dir_id, doc_id, chunk_index, chunk_id, bytez, stub):
        data_block = kvstore_pb2.DataBlock(key=chunk_id, value=bytez)

        for _ in range(3):
            save_status = stub.Save(data_block)
            if save_status.status == 'success':
                break

        # save to database
        self.db.save_chunk(dir_id, doc_id, chunk_index, chunk_id)

    def __readbytes(self, dir_id, doc_id, stub):
        chunks = self.get_chunk_metadata(dir_id, doc_id)
        bytez = bytes()
        for chunk in chunks:
            data = self.__readchunk(chunk[3], stub)
            bytez += data
        return bytez

    def __uploadbytes(self, dir_id, doc_id, bytez, stub):
        for chunk_index, start in enumerate(range(0, len(bytez), KV_STORE_BLOCK_SIZE)):
            block = bytez[start : min(len(bytez), start + KV_STORE_BLOCK_SIZE)]
            self.__uploadblock(dir_id, doc_id, chunk_index, generateId(), block, stub)
            

    def __uploadfile(self, dir_id, filepath, stub):
        for chunk_index, chunk in file_iterator(filepath):
            self.__uploadblock(dir_id, filepath, chunk_index, generateId(), chunk.encode(KV_STORE_ENCODING), stub)


    def __uploadfilestr(self, dir_id, doc_id, string, stub):
        for chunk_index, chunk in str_iterator(string):
            self.__uploadblock(dir_id, doc_id, chunk_index, generateId(), chunk.encode(KV_STORE_ENCODING), stub)


    def __uploaddirectory(self, dirpath, stub):
        # create an id to keep all files in the directory together on the server
        # all the files can be accessed using this id
        dir_id = generateId()
            
        # recursively upload all the files in the given directory
        for r, d, f in os.walk(dirpath):
            for file in f:
                filepath = os.path.join(r, file)
                self.__uploadfile(dir_id, filepath, stub)
        return dir_id


    def __readchunk(self, chunk_id, stub):
        return stub.Get(kvstore_pb2.Id(id = chunk_id)).value


    def __downloadfile(self, dir_id, doc_id, root, flatten, stub):
        save_path = os.path.join(root, os.path.basename(doc_id) if flatten else doc_id)

        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        
        with open(save_path, 'w') as f:
            chunks = self.get_chunk_metadata(dir_id, doc_id)
            for chunk in chunks:
                data = self.__readchunk(chunk[3], stub).decode(KV_STORE_ENCODING)
                f.write(data)


    def __downloaddirectory(self, dir_id, save_path, flatten, stub):
        docs = self.get_doc_metadata(dir_id)
        for doc_id in docs:
            self.download_file(dir_id, doc_id[0], save_path, flatten, stub)


    def close(self, channel):
        channel.close()

# if __name__ == "__main__":
#     rm = ResourceManager()
#     k = KeyValueStoreClient(rm.find_kvstore())
#     dir_id = k.upload_directory(sys.argv[1])
#     k.download_directory(dir_id, 'hi-there')

#     s = k.read_bytes('1d140d8f-1918-4ae3-b0da-fefb3fec7fb0-191110-150149', 'd4299dba-7530-4f19-bb06-463aacf5bdd2-191110-150152')
#     print(pickle.loads(s))

#     dir_id = generateId()
#     doc_id = generateId()

#     d = {'hi': [1, 2, 3], 'hello': [4, 5, 6]}
#     k.upload_bytes(dir_id, doc_id, pickle.dumps(d))

#     x = pickle.loads(k.read_bytes(dir_id, doc_id))
#     print(x)
    
