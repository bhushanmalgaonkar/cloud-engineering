#!/usr/bin/python3

import os
import grpc
import time
import pickle
import threading
import logging as log
from queue import Queue
from random import shuffle
from concurrent import futures

from resource_manager import ResourceManager
import mapreduce_pb2, mapreduce_pb2_grpc
import kvstore_pb2, kvstore_pb2_grpc
from constants import MAP_REDUCE_MASTER_PORT, WORKERS, NUM_WORKERS, TASKS_PER_WORKER
from kvstore_client import KeyValueStoreClient
from util import generateId
from gcloud_util import *

def task_str(task):
    return 'Task: code_id={}, type={}, input_dir_id={}, input_doc_id={}, input_chunk_id={}, \
                        output_dir_id={}, output_doc_id={}'.format(task.code_id, task.type, 
                            task.input_dir_id, task.input_doc_id, task.input_chunk_id, 
                            task.output_dir_id, task.output_doc_id)

def worker_str(worker):
    return 'Worker: {}:{}'.format(worker[0], worker[1])

class Listener(mapreduce_pb2_grpc.MapReduceMasterServicer):
    def __init__(self, *args, **kwargs):
        log.info("Initializing MapReduceMaster")
        self.rm = ResourceManager()

        self.KV_STORE_HOST = self.rm.find_kvstore()
        self.kvstore = KeyValueStoreClient(self.KV_STORE_HOST)

        self.workers = Queue()
        self.workers_mutex = threading.Lock()

        log.info("Initializing MapReduceMaster is complete, KV_STORE_HOST: {}".format(self.KV_STORE_HOST))

    def SubmitJob(self, job, context):

        # create new execution id
        exec_id = generateId()
        log.info('Received job: code_id:{} data_id:{}. Results will be stored under:{}'\
            .format(job.code_id, job.data_id, exec_id))
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'Received job')

        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'Setting up workers')
        self.__launch_workers()
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'Setting up workers is complete')

        # get all chunk ids from database
        log.info('Downloading chunk metadata from KeyValueStore')
        chunks = self.kvstore.get_chunk_metadata(job.data_id)
        worker_threads = []
        
        # send chunk_id and code_id to available worker
        mapper_outputs = []
        for idx, chunk in enumerate(chunks):
            worker = self.__getworker()
            
            status = 'map_task {}/{} --> {}'.format(idx + 1, len(chunks), worker)
            log.info(status)
            yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = status)
            
            # create new doc_id to store intermediate mapper output
            mapper_output_doc_id = generateId()
            mapper_outputs.append(mapper_output_doc_id)
            task = mapreduce_pb2.Task(code_id=job.code_id, type='map', \
                input_dir_id=exec_id, input_doc_id=chunk[1], input_chunk_id=chunk[3], \
                output_dir_id=exec_id, output_doc_id=mapper_output_doc_id)

            log.debug(task_str(task))
            log.debug(worker_str(worker))

            # start task in thread
            wthread = threading.Thread(target=self.__execute_chunk, args=(worker, task, ), daemon=True)
            wthread.start()
            worker_threads.append(wthread)

        # wait for all threads to finish
        for wthread in worker_threads:
            wthread.join()

        status = 'All map_tasks finished'
        log.info(status)
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = status)

        shuffled_output = {}
        for doc_id in mapper_outputs:
            data = self.kvstore.read_bytes(exec_id, doc_id)
            if data:
                output = pickle.loads(data)
                for entry in output:
                    if entry[0] not in shuffled_output:
                        shuffled_output[entry[0]] = []
                    shuffled_output[entry[0]].append(entry[1])

        shuffled_output_doc_id = generateId()
        self.kvstore.upload_bytes(exec_id, shuffled_output_doc_id, pickle.dumps(shuffled_output))

        status = 'Shuffling and sorting of mapper outputs is complete.'
        log.info(status)      
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = status)

        worker = self.__getworker()
        reducer_output_doc_id = 'output'
        task = mapreduce_pb2.Task(code_id=job.code_id, type='reduce', \
            input_dir_id=exec_id, input_doc_id=shuffled_output_doc_id, input_chunk_id='', \
            output_dir_id=exec_id, output_doc_id=reducer_output_doc_id)

        # start task in thread
        wthread = threading.Thread(target=self.__execute_chunk, args=(worker, task, ), daemon=True)
        wthread.start()

        status = 'reduce_task --> {}'.format(worker)
        log.info(status)
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = status)

        wthread.join()
        status = 'reduce_task finished.'
        log.info(status)
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = status)

        status = 'Success'
        log.info(status)
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = status)

        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'Cleaning up workers')
        self.rm.destroy_workers()
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'Cleaning up workers is complete')

    def __getworker(self):
        log.info("Waiting for worker")
        worker = None

        # loop until we successfully acquire a worker
        while not worker:
            # check if worker is still available
            self.workers_mutex.acquire()
            if not self.workers.empty():
                worker = self.workers.get()
            else:
                log.info('all workers busy, wait..')
            self.workers_mutex.release()

            if not worker:
                time.sleep(1)

        log.info("Got one worker")
        return worker

    def __execute_chunk(self, worker, task):
        try:
            # assign chunk to worker
            with grpc.insecure_channel("{}:{}".format(worker[0], worker[1])) as channel:
                stub = mapreduce_pb2_grpc.MapReduceWorkerStub(channel)
                log.debug('Completed ' + task_str(task))
                return stub.Execute(task)
        except BaseException as e:
            print(e)
            log.error('Error executing ' + task_str(task) + ', ' + str(e))
        finally:
            # return the work to the pool
            self.workers_mutex.acquire()
            self.workers.put(worker)
            self.workers_mutex.release()

    def __launch_workers(self):
        log.info("Creating workers")
        worker_list = self.rm.create_workers(NUM_WORKERS)
        log.info("Workers created" + str(worker_list))
        shuffle(worker_list)

        self.workers = Queue()
        for worker in worker_list:
            for _ in range(TASKS_PER_WORKER):
                self.workers.put(worker)

def run_mapreduce_master(port=MAP_REDUCE_MASTER_PORT):
    if not os.path.exists('logs') or not os.path.isdir('logs'):
        os.makedirs('logs')

    level = log.DEBUG
    log.basicConfig(format='%(levelname)s: %(message)s',
                        level=level, filename='logs/master-{}.log'.format(port))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    mapreduce_pb2_grpc.add_MapReduceMasterServicer_to_server(Listener(), server)
    server.add_insecure_port("0.0.0.0:{}".format(port))
    server.start()
    print('MapReduce server listening on port {}'.format(port))

    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt on master:{}".format(port))
            log.info('KeyboardInterrupt')
            server.stop(0)
            break
        except:
            pass


if __name__ == "__main__":
    run_mapreduce_master()