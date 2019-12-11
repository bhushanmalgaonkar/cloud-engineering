#!/usr/bin/python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging as log

from gcloud_util import *

from constants import GCLOUD_PROJECT, GCLOUD_REGION, GCLOUD_ZONE

from googleapiclient.discovery import build

compute = build('compute', 'v1')

def test_worker_boot_disk_methods():
    disk_name = 'test-disk'

    try:
        create_worker_boot_disk(disk_name, wait=True)

        # check if disk is created
        disk_list = compute.disks().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
        disk_names = [disk['name'] for disk in disk_list['items']]

        result = 'Test {}: create_worker_boot_disk'.format('passed' if disk_name in disk_names else 'failed')
        print(result)
        log.info(result)
    except Exception as e:
        log.error('Error creating disk: {}'.format(str(e)))
    finally:
        delete_disk(disk_name, wait=True)

        # check if disk is deleted
        disk_list = compute.disks().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
        disk_names = [disk['name'] for disk in disk_list['items']]

        result = 'Test {}: delete_disk'.format('passed' if disk_name not in disk_names else 'failed')
        print(result)
        log.info(result)

def test_worker_instance_methods():
    worker_name = 'test-worker'

    try:
        create_worker_instance(worker_name, wait=True)

        # check if instance is created
        instance_list = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
        instance_names = [instance['name'] for instance in instance_list['items']]

        result = 'Test {}: create_worker_instance'.format('passed' if worker_name in instance_names else 'failed')
        print(result)
        log.info(result)


        stop_instance(worker_name, wait=True)

        # check if instance is terminated
        instance_list = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
        instance_status = {instance['name']:instance['status'] for instance in instance_list['items']}

        result = 'Test {}: stop_instance'.format('passed' if instance_status[worker_name] == 'TERMINATED' else 'failed')
        print(result)
        log.info(result)


        start_instance(worker_name, wait=True)

        # check if instance is started
        instance_list = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
        instance_status = {instance['name']:instance['status'] for instance in instance_list['items']}

        result = 'Test {}: start_instance'.format('passed' if instance_status[worker_name] == 'RUNNING' else 'failed')
        print(result)
        log.info(result)
    except Exception as e:
        print(e)
        log.error('Error creating instance: {}'.format(str(e)))
    finally:
        delete_instance(worker_name, wait=True)

        # check if instance is deleted
        instance_list = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
        instance_names = [instance['name'] for instance in instance_list['items']]

        result = 'Test {}: delete_instance'.format('passed' if worker_name not in instance_names else 'failed')
        print(result)
        log.info(result)


if __name__ == "__main__":
    level = log.DEBUG
    log.basicConfig(format='%(levelname)s: %(message)s',
                        level=level, filename='tests.log')

    # test_worker_boot_disk_methods()
    test_worker_instance_methods()