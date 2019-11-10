#!/usr/bin/python3

import os
import sys
import grpc

import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_HOST, KV_STORE_PORT, KV_STORE_DB_PATH, KV_STORE_ENCODING, KV_STORE_BLOCK_SIZE
from database_handler import DataBaseHandler
from util import generateId, file_iterator, str_iterator

class KeyValueStoreClient:
    def __init__(self):
        self.db = DataBaseHandler(KV_STORE_DB_PATH)

    '''
        Upload a bytes object as document
    '''
    def upload_bytes(self, dir_id, doc_id, bytez, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadbytes(dir_id, doc_id, bytez, stub)
                channel.unsubscribe(self.close)
        else:
            self.__uploadbytes(dir_id, doc_id, bytez, stub)

    '''
        Reads a text file and saves it in key-value store
    '''
    def upload_file(self, dir_id, filepath, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
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
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__uploadfilestr(dir_id, doc_id, string, stub)
                channel.unsubscribe(self.close)
        else:
            self.__uploadfilestr(dir_id, doc_id, string, stub)

    '''
        Upload an entire directory
    '''
    def upload_directory(self, dirpath, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                dir_id = self.__uploaddirectory(dirpath, stub)
                channel.unsubscribe(self.close)
        else:
            dir_id = self.__uploaddirectory(dirpath, stub)
        return dir_id 

    '''
        Saves all the files associated with dir_id at save_path
    '''
    def download_directory(self, dir_id, save_path, flatten=False, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__downloaddirectory(dir_id, save_path, flatten, stub)
                channel.unsubscribe(self.close)
        else:
            self.__downloaddirectory(dir_id, save_path, flatten, stub)

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
        Downloads a chunk given chunk_id and saves it as file save_path
    '''
    def download_chunk(self, chunk_id, save_path, stub=None):
        if not stub:
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
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
            with grpc.insecure_channel("{}:{}".format(KV_STORE_HOST, KV_STORE_PORT)) as channel:
                stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)
                self.__readchunk(chunk_id, stub)
        else:
            self.__readchunk(chunk_id, stub)


        
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
        print('kvstore: saved {} {} {} {}'.format(dir_id, doc_id, chunk_index, chunk_id))


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
        print('kvstore: dir_id: {}'.format(dir_id))
            
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


if __name__ == "__main__":
    k = KeyValueStoreClient()
    dir_id = k.upload_directory(sys.argv[1])
    k.download_directory(dir_id, 'save_path', flatten=False)