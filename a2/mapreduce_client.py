#!/usr/bin/python3

import os
import sys
import grpc
import argparse
import logging as log

import mapreduce_pb2, mapreduce_pb2_grpc
from kvstore_client import KeyValueStoreClient
from constants import MAP_REDUCE_MASTER_HOST, MAP_REDUCE_MASTER_PORT

def close(channel):
    channel.close()

def submit_job(dir_data, dir_code, dir_output):
    log.info('New job submitted: dir_data={}, dir_code={}, dir_output={}'.format(dir_data, dir_code, dir_output))
    try:
        print('reading data from        : ', dir_data)
        print('reading code from        : ', dir_code)
        print('output will be saved at  : ', dir_output)

        # upload data and code to key-value store
        kv_store = KeyValueStoreClient()
        data_id = kv_store.upload_directory(dir_data)
        code_id = kv_store.upload_directory(dir_code)

        print('data is saved with data_id: ', data_id)
        print('code is saved with code_id: ', code_id)
        log.debug('data_id={}'.format(data_id))
        log.debug('code_id={}'.format(code_id))

        # rpc call submit job with data_id and code_id
        with grpc.insecure_channel("{}:{}".format(MAP_REDUCE_MASTER_HOST, MAP_REDUCE_MASTER_PORT)) as channel:
            stub = mapreduce_pb2_grpc.MapReduceMasterStub(channel)

            exec_info = stub.SubmitJob(mapreduce_pb2.Job(code_id = code_id, data_id = data_id))
            for info in exec_info:
                print('master:', info.status)
                log.debug('job status from master: {}'.format(info.status))

            channel.unsubscribe(close)
        log.info('map-reduce task is finished. downloading output')

        # save output to dir_output
        kv_store.download_file(info.exec_id, 'output', dir_output)
        print('downloading {}'.format(info.exec_id))
        log.info('output is written to {}'.format(dir_output))
    except BaseException as e:
        print('mrclient: Failed submitting the job. Error: {}'.format(e))
        log.error('error on master: {}'.format(e))


if __name__ == "__main__":

    level = log.DEBUG
    log.basicConfig(format='%(levelname)s: %(message)s',
                        level=level, filename='logs/client.log')

    parser = argparse.ArgumentParser(description="MapReduce Client")
    parser.add_argument('-d', '--data', type=str,
                        help='directory which contains all the input files')
    parser.add_argument('-c', '--code', type=str,
                        help='directory which contains code file')
    parser.add_argument('-o', '--output', type=str,
                        help='directory where final output will be stored')
    args = parser.parse_args()
    
    dir_data = args.data
    dir_code = args.code
    dir_output = args.output

    if not dir_data or not os.path.exists(dir_data) or not os.path.isdir(dir_data):
        print('run {} -h for usage'.format(sys.argv[0]))
        exit(1)
    if not dir_code or not os.path.exists(dir_code) or not os.path.isdir(dir_code):
        print('run {} -h for usage'.format(sys.argv[0]))
        exit(1)

    submit_job(dir_data, dir_code, dir_output)