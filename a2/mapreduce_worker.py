#!/usr/bin/python3

import os
import sys
import grpc
import shutil
import pickle
import time
import argparse
import logging as log
from concurrent import futures
from random import random

import mapreduce_pb2, mapreduce_pb2_grpc
import kvstore_pb2, kvstore_pb2_grpc
from constants import KV_STORE_ENCODING, INTERMEDIATE_OUTPUTS_DIR, TASKS_PER_WORKER
from kvstore_client import KeyValueStoreClient
from util import generateId
from resource_manager import ResourceManager

class Listener(mapreduce_pb2_grpc.MapReduceWorkerServicer):
    def __init__(self, *args, **kwargs):
        self.rm = ResourceManager()
        self.kvstore = KeyValueStoreClient(self.rm.find_kvstore())

    def Execute(self, task, context):
        print('Execute request. code_id:{}, chunk_id:{}, type:{}'.format(task.code_id, task.input_chunk_id, task.type))
        log.info('Execute request. code_id:{}, chunk_id:{}, type:{}'.format(task.code_id, task.input_chunk_id, task.type))
        
        # download code and chunk
        log.info('Downloadin chunk')
        workplace = os.path.join(INTERMEDIATE_OUTPUTS_DIR, task.output_doc_id)
        self.kvstore.download_directory(task.code_id, workplace, flatten=True)

        log.info('Downloading code')
        module_name = generateId()
        os.rename(os.path.join(workplace, 'task.py'), os.path.join(workplace, module_name + '.py'))

        try:
            sys.path.insert(1, workplace)
            py = __import__(module_name)

            output = []
            if task.type == 'map':
                chunk = self.kvstore.read_chunk(task.input_chunk_id).decode(KV_STORE_ENCODING)
                for ch in py.mapper(task.input_doc_id, chunk):
                    output.append(ch)
                
                self.kvstore.upload_bytes(task.output_dir_id, task.output_doc_id, pickle.dumps(output))
            elif task.type == 'reduce':
                chunk = pickle.loads(self.kvstore.read_bytes(task.input_dir_id, task.input_doc_id))
                for ch in py.reducer(chunk):
                    output.append('{} {}'.format(ch[0], ch[1]))
                
                self.kvstore.upload_file_str(task.output_dir_id, task.output_doc_id, '\n'.join(output))
            else:
                raise 'unknown operation'

            log.info('success')
            return mapreduce_pb2.ExecutionInfo(exec_id=task.output_dir_id, status='success')
        except BaseException as e:
            log.info('task failed {}'.format(e))
            return mapreduce_pb2.ExecutionInfo(exec_id=task.output_dir_id, status='failed')
        finally:
            shutil.rmtree(workplace)
            
def run_mapreduce_worker(port):
    if not os.path.exists('logs') or not os.path.isdir('logs'):
        os.makedirs('logs')

    level = log.DEBUG
    log.basicConfig(format='%(levelname)s: %(message)s',
                        level=level, filename='logs/worker-{}.log'.format(port))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=TASKS_PER_WORKER))
    mapreduce_pb2_grpc.add_MapReduceWorkerServicer_to_server(Listener(), server)
    server.add_insecure_port("0.0.0.0:{}".format(port))
    server.start()
    print('MapReduce worker listening on port {}'.format(port))

    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt on worker:{}".format(port))
            log.info('KeyboardInterrupt')
            server.stop(0)
            break
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MapReduceWorker")
    parser.add_argument('-p', '--port', type=int,
                        help='start worker on port <port>')
    args = parser.parse_args()
    run_mapreduce_worker(args.port)