#!/usr/bin/python3

import grpc
import argparse
from concurrent import futures

import mapreduce_pb2, mapreduce_pb2_grpc
from constants import MAP_REDUCE_MASTER_PORT, KV_STORE_DB_PATH
from database_handler import DataBaseHandler

class Listener(mapreduce_pb2_grpc.MapReduceMasterServicer):
    def __init__(self, *args, **kwargs):
        self.db = DataBaseHandler(KV_STORE_DB_PATH)

    def SubmitJob(self, job, context):
        yield mapreduce_pb2.ExecutionInfo(exec_id = 'hi there', status = 'Received job {} {}'.format(job.code_id, job.data_id))

        # get all chunk ids from database
        chunks = self.db.get_chunk_metadata(job.data_id)
        
        # send chunk_id and code_id to available mapper

def run_server(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
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