#!/usr/bin/python3

import os
import sys
import grpc
import shutil
import argparse
import tempfile
from concurrent import futures

import mapreduce_pb2, mapreduce_pb2_grpc
import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_DB_PATH, KV_STORE_HOST, KV_STORE_PORT, INTERMEDIATE_OUTPUTS_DIR
from database_handler import DataBaseHandler
from kvstore_client import KeyValueStoreClient

class Listener(mapreduce_pb2_grpc.MapReduceWorkerServicer):
    def __init__(self, *args, **kwargs):
        self.db = DataBaseHandler(KV_STORE_DB_PATH)
        self.kvstore = KeyValueStoreClient()

    def Execute(self, task, context):
        print('Execute request.', task.code_id, task.doc_id)
        
        # download code and chunk
        workplace = os.path.join(INTERMEDIATE_OUTPUTS_DIR, task.dir_id)
        self.kvstore.download_directory(task.code_id, workplace, flatten=True)
        chunk = self.kvstore.read_chunk(task.chunk_id)
        
        print('download complete')

        try:
            sys.path.insert(1, workplace)
            py = __import__('task')
        
            output = []
            if task.type == 'map':
                print('Performing map')
                for ch in py.mapper(chunk):
                    output.append('{} {}'.format(ch[0], ch[1]))
            elif task.type == 'reduce':
                print('Performing reduce')
                for ch in py.reducer(chunk):
                    output.append('{} {}'.format(ch[0], ch[1]))

            self.kvstore.upload_file_str(task.dir_id, task.doc_id, '\n'.join(output))
            return mapreduce_pb2.ExecutionInfo(exec_id=task.dir_id, status='success')
        except BaseException as e:
            print(e)
            return mapreduce_pb2.ExecutionInfo(exec_id=task.dir_id, status='failed')
        finally:
            shutil.rmtree(workplace)

def run_server(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    mapreduce_pb2_grpc.add_MapReduceWorkerServicer_to_server(Listener(), server)
    server.add_insecure_port("[::]:{}".format(port))
    server.start()
    print('MapReduce worker listening on port {}'.format(port))

    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            server.stop(0)
            break
        except:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MapReduceWorker")
    parser.add_argument('-p', '--port', type=int,
                        help='start worker on port <port>')
    args = parser.parse_args()
    run_server(args.port)