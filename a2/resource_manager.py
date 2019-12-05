#!/usr/bin/python3

from gcloud_util import *
from constants import *

class ResourceManager:
    def create_workers(self, num_workers):
        WORKERS = []
        for idx in range(num_workers):
            instance_name = 'worker-{}'.format(idx)
            create_worker_instance(instance_name, wait=True)
            ip = get_instance_ip(instance_name)
            WORKERS.append((ip, MAP_REDUCE_WORKER_PORT))

        return WORKERS

    def destroy_workers(self):
        instances = list_instances()
        for name, info in instances.items():
            if info['type'] == 'map-reduce-worker':
                delete_instance(name, wait=True)

    def find_kvstore(self):
        print('Finding kvstore')
        instances = list_instances()
        if 'key-value-store' not in instances:
            raise Exception('key-value-store instance does not exist')
        key_value_store = instances['key-value-store']
        if key_value_store['status'] != 'RUNNING':
            raise Exception('key-value-store server is not running')
        
        return key_value_store['ip']

    def find_mapreduce_master(self):
        instances = list_instances()
        if 'map-reduce-master' not in instances:
            raise Exception('map-reduce-master instance does not exist')
        map_reduce_master = instances['map-reduce-master']
        if map_reduce_master['status'] != 'RUNNING':
            raise Exception('map-reduce-master is not running')
        
        return map_reduce_master['ip']

    def find_mapreduce_workers(self):
        WORKERS = []

        instances = list_instances()
        for name, info in instances.items():
            if info['type'] == 'map-reduce-worker' and info['status'] == 'RUNNING':
                WORKERS.append((info['ip'], MAP_REDUCE_WORKER_PORT))

        print('WORKERS = {}'.format(WORKERS))

if __name__ == "__main__":
    rm = ResourceManager()
    print(rm.create_workers(1))