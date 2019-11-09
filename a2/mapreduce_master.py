#!/usr/bin/python3

import grpc
import time
import argparse
from queue import Queue
from concurrent import futures
import threading

import mapreduce_pb2, mapreduce_pb2_grpc
from constants import MAP_REDUCE_MASTER_PORT, KV_STORE_DB_PATH, WORKERS
from database_handler import DataBaseHandler
from util import generateId

workers = Queue()
for worker in WORKERS:
    workers.put(worker)

workers_mutex = threading.Lock()

class Listener(mapreduce_pb2_grpc.MapReduceMasterServicer):
    def __init__(self, *args, **kwargs):
        self.db = DataBaseHandler(KV_STORE_DB_PATH)

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
        print('mrmaster: Received job {} {}'.format(job.code_id, job.data_id))

        # create new execution id
        exec_id = generateId()
        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = 'Received')

        # get all chunk ids from database
        chunks = self.db.get_chunk_metadata(job.data_id)
        print('mrmaster: chunks: ', chunks)

        worker_threads = []
        
        # send chunk_id and code_id to available worker
        mapper_outputs = []
        for idx, chunk in enumerate(chunks):
            worker = None

            # loop until we successfully acquire a worker
            while not worker:
                while workers.empty():
                    print('all mappers busy, wait..')
                    time.sleep(2)

                workers_mutex.acquire()
                if not workers.empty():
                    worker = workers.get()
                workers_mutex.release()

            yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = '{}/{} map tasks finished'.format(idx, len(chunks)))
            print('Found worker: ', worker)

            # create new doc_id to store intermediate mapper output
            doc_id = generateId()
            mapper_outputs.append(doc_id)
            task = mapreduce_pb2.Task(code_id=job.code_id, chunk_id=chunk[3], type='map', dir_id=exec_id, doc_id=doc_id)
            
            # start task in thread
            wthread = threading.Thread(target=self.__execute_chunk, args=(worker, task, ), daemon=True)
            wthread.start()
            worker_threads.append(wthread)

        # wait for all threads to finish
        for wthread in worker_threads:
            wthread.join()

        yield mapreduce_pb2.ExecutionInfo(exec_id = exec_id, status = '{}/{} map tasks finished'.format(len(chunks), len(chunks)))

        print('mrmaster: Finished job {} {}'.format(job.code_id, job.data_id))
        yield mapreduce_pb2.ExecutionInfo(exec_id = 'save_path', status = 'Finished job {} {}'.format(job.code_id, job.data_id))

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