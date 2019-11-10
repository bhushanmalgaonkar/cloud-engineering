#!/usr/bin/python3

import grpc
import time
import pickle
import argparse
from queue import Queue
from concurrent import futures
import threading

import mapreduce_pb2, mapreduce_pb2_grpc
import kvstore_pb2, kvstore_pb2_grpc
from constants import MAP_REDUCE_MASTER_PORT, KV_STORE_DB_PATH, WORKERS
from kvstore_client import KeyValueStoreClient
from util import generateId

workers = Queue()
for worker in WORKERS:
    workers.put(worker)

workers_mutex = threading.Lock()

class Listener(mapreduce_pb2_grpc.MapReduceMasterServicer):
    def __init__(self, *args, **kwargs):
        self.kvstore = KeyValueStoreClient()

    def __execute_chunk(self, worker, task):
        try:
            # assign chunk to worker
            with grpc.insecure_channel("{}:{}".format(worker[0], worker[1])) as channel:
                stub = mapreduce_pb2_grpc.MapReduceWorkerStub(channel)
                return stub.Execute(task)
        except BaseException as e:
            print(e)
        finally:
            # return the work to the pool
            workers_mutex.acquire()
            workers.put(worker)
            workers_mutex.release()

    def SubmitJob(self, job, context):
        print('received job {} {}'.format(job.code_id, job.data_id))

        # create new execution id
        exec_id = generateId()
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'received job')

        # get all chunk ids from database
        chunks = self.kvstore.get_chunk_metadata(job.data_id)
        worker_threads = []
        
        # send chunk_id and code_id to available worker
        mapper_outputs = []
        for idx, chunk in enumerate(chunks):
            worker = self.__getworker()
            yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = '{}/{} map tasks finished'.format(idx, len(chunks)))
            
            # create new doc_id to store intermediate mapper output
            doc_id = generateId()
            mapper_outputs.append(doc_id)
            task = mapreduce_pb2.Task(code_id=job.code_id, chunk_id=chunk[3], type='map', \
                input_doc_id=chunk[1], output_dir_id=exec_id, output_doc_id=doc_id)
            
            # start task in thread
            wthread = threading.Thread(target=self.__execute_chunk, args=(worker, task, ), daemon=True)
            wthread.start()
            worker_threads.append(wthread)

        # wait for all threads to finish
        for wthread in worker_threads:
            wthread.join()

        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = '{}/{} map tasks finished'.format(len(chunks), len(chunks)))

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
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'shuffling and sorting of mapper outputs is complete.')

        worker = self.__getworker()
        reducer_output_doc_id = 'output'
        task = mapreduce_pb2.Task(code_id=job.code_id, chunk_id=shuffled_output_doc_id, type='reduce', \
            input_doc_id='', output_dir_id=exec_id, output_doc_id=reducer_output_doc_id)

        # start task in thread
        wthread = threading.Thread(target=self.__execute_chunk, args=(worker, task, ), daemon=True)
        wthread.start()
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'reducer task started.')

        wthread.join()
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'reducer task finished.')

        # shuffled_output_doc_id = generateId()
        # shuffled_output_chunk_ids = []
        # for chunk_index, chunk in dict_iterator(shuffled_output):
        #     chunk_id = generateId()
        #     self.kvstore.upload_block(exec_id, shuffled_output_doc_id, chunk_index, chunk_id, pickle.dumps(chunk))
        #     shuffled_output_chunk_ids.append(chunk_id)

        # yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'saved shuffled output.')

        # reducer_output_doc_id = 'output'
        # worker_threads = []
        # for idx, chunk_id in enumerate(shuffled_output_chunk_ids):
        #     worker = self.__getworker()
        #     yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, \
        #         status = '{}/{} reduce tasks finished.'.format(idx, len(shuffled_output_chunk_ids)))

        #     # create new doc_id to store intermediate mapper output
        #     task = mapreduce_pb2.Task(code_id=job.code_id, chunk_id=chunk_id, type='reduce', dir_id=exec_id, doc_id=reducer_output_doc_id)

        #     # start task in thread
        #     wthread = threading.Thread(target=self.__execute_chunk, args=(worker, task, ), daemon=True)
        #     wthread.start()
        #     worker_threads.append(wthread)

        # # wait for all worker threads to finish
        # for wthread in worker_threads:
        #     wthread.join()

        # yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, \
        #         status = '{}/{} reduce tasks finished.'.format(len(shuffled_output_chunk_ids), len(shuffled_output_chunk_ids)))

        print('success')
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'success')

    def __getworker(self):
        worker = None

        # loop until we successfully acquire a worker
        while not worker:
            # check if worker is still available
            workers_mutex.acquire()
            if not workers.empty():
                worker = workers.get()
            else:
                print('all workers busy, wait..')
            workers_mutex.release()

            if not worker:
                time.sleep(2)
        return worker

def run_server(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    mapreduce_pb2_grpc.add_MapReduceMasterServicer_to_server(Listener(), server)
    server.add_insecure_port("[::]:{}".format(port))
    server.start()
    print('MapReduce server listening on port {}'.format(port))

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
    # parser = argparse.ArgumentParser(description="MapReduce")
    # parser.add_argument('-p', '--port', type=int, default=MAP_REDUCE_MASTER_PORT,
    #                     help='listen on/connect to port <port> (default={}'
    #                     .format(MAP_REDUCE_MASTER_PORT))
    # args = parser.parse_args()

    # port = args['port']
    run_server(MAP_REDUCE_MASTER_PORT)