#!/usr/bin/python3

from gcloud_util import *
from constants import *

class ResourceManager:
    def create_workers(self, num_workers):

        create_disk_operations = []
        for idx in range(num_workers):
            disk_name = 'worker-{}'.format(idx)
            operation = create_worker_boot_disk(disk_name, wait=False)
            create_disk_operations.append(operation)
        
        # wait until all disks are created
        for operation in create_disk_operations:
            wait_for_operation(operation)

        create_operations = []
        for idx in range(num_workers):
            instance_name = 'worker-{}'.format(idx)
            operation = create_worker_instance(instance_name, disk_name=instance_name, wait=False)
            create_operations.append(operation)
            print('created worker-{}'.format(idx))

        # wait until all instances are running
        for idx, operation in enumerate(create_operations):
            wait_for_operation(operation)
            print('worker-{} is running'.format(idx))

        # wait until all instances are ssh ready
        WORKERS = []
        for idx in range(num_workers):
            instance_name = 'worker-{}'.format(idx)
            ip = get_instance_ip(instance_name)
            wait_port_open(ip, 22)
            WORKERS.append((ip, MAP_REDUCE_WORKER_PORT))
            print('worker-{} is ssh ready'.format(idx))
        
        log.info("Waiting 5 sec for startup-script to complete")
        time.sleep(5)

        return WORKERS

    def destroy_workers(self):
        instances = list_instances()

        delete_operations = []
        for name, info in instances.items():
            if info['type'] == 'map-reduce-worker':
                operation = delete_instance(name, wait=False)
                delete_operations.append(operation)
        
        for operation in delete_operations:
            wait_for_operation(operation)

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
    # print(rm.create_workers(5))
    rm.destroy_workers()