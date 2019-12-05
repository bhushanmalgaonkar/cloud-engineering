#!/usr/bin/python3

import time
import socket
import logging as log

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from constants import MAP_REDUCE_WORKER_PORT, USER

GCLOUD_PROJECT = 'bhushan-malgaonkar'
GCLOUD_REGION = 'us-central1'
GCLOUD_ZONE = 'us-central1-c'

WORKER_DISK_NAME = 'base-snapshot'

compute = build('compute', 'v1')

def create_worker_boot_disk(disk_name, wait=False):
    log.info("Creating worker boot disk {}".format(disk_name))

    disk_body = {
        "name": disk_name,
        "sourceSnapshot": "projects/{}/global/snapshots/{}".format(GCLOUD_PROJECT, WORKER_DISK_NAME),
        "sizeGb": "10",
        "type": "projects/{}/zones/{}/diskTypes/pd-standard".format(GCLOUD_PROJECT, GCLOUD_ZONE),
        "zone": "projects/{}/zones/{}".format(GCLOUD_PROJECT, GCLOUD_ZONE)
    }

    response = compute.disks().insert(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, body=disk_body).execute()
    if wait:
        response = wait_for_operation(response)

    log.info("Creating worker boot disk {} is successful".format(disk_name))
    return response

def delete_disk(disk_name, wait=False):
    log.info("Deleting disk {}".format(disk_name))

    response = compute.disks().delete(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, disk=disk_name).execute()
    if wait:
        response = wait_for_operation(response)

    log.info("Deleting disk {} is successful".format(disk_name))
    return response

def create_worker_instance(instance_name, disk_name=None, wait=False):
    log.info("Creating worker instance {}".format(disk_name))

    if not disk_name:
        disk_name = instance_name
        create_worker_boot_disk(disk_name, wait=True)

    instance_body = {
        "kind": "compute#instance",
        "name": instance_name,
        "zone": "projects/{}/zones/{}".format(GCLOUD_PROJECT, GCLOUD_ZONE),
        "machineType": "projects/{}/zones/{}/machineTypes/n1-standard-1".format(GCLOUD_PROJECT, GCLOUD_ZONE),
        "displayDevice": {
            "enableDisplay": False
        },
        "metadata": {
            "items": [
                {
                "key": "startup-script",
                "value": "#! /bin/bash\nsleep 1m\npython3 /home/{}/a2/mapreduce_worker.py -p {}".format(USER, MAP_REDUCE_WORKER_PORT)
                }
            ]
        },
        "disks": [
            {
            "kind": "compute#attachedDisk",
            "type": "PERSISTENT",
            "boot": True,
            "mode": "READ_WRITE",
            "autoDelete": True,
            "deviceName": instance_name,
            "source": "projects/{}/zones/{}/disks/{}".format(GCLOUD_PROJECT, GCLOUD_ZONE, disk_name)
            }
        ],
        "canIpForward": False,
        "networkInterfaces": [
            {
            "kind": "compute#networkInterface",
            "subnetwork": "projects/{}/regions/{}/subnetworks/default".format(GCLOUD_PROJECT, GCLOUD_REGION),
            "accessConfigs": [
                {
                "kind": "compute#accessConfig",
                "name": "External NAT",
                "type": "ONE_TO_ONE_NAT",
                "networkTier": "PREMIUM"
                }
            ],
            "aliasIpRanges": []
            }
        ],
        "labels": {
            "type": "map-reduce-worker"
        },
        "scheduling": {
            "preemptible": False,
            "onHostMaintenance": "MIGRATE",
            "automaticRestart": True,
            "nodeAffinities": []
        },
        "deletionProtection": False,
        "reservationAffinity": {
            "consumeReservationType": "ANY_RESERVATION"
        },
        "serviceAccounts": [
            {
                "email": "1093190347201-compute@developer.gserviceaccount.com",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/servicecontrol",
                    "https://www.googleapis.com/auth/service.management.readonly",
                    "https://www.googleapis.com/auth/trace.append",
                    "https://www.googleapis.com/auth/compute"
                ]
            }
        ]
    }
    response = compute.instances().insert(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, body=instance_body).execute()
    if wait:
        response = wait_for_operation(response)
        wait_port_open(get_instance_ip(instance_name), 22)

        log.info("Waiting 5 sec for startup-script to complete")
        time.sleep(5)

    log.info("Creating worker instance {} is successful".format(disk_name))
    return response

def start_instance(instance_name, wait=False):
    log.info("Starting instance {}".format(instance_name))

    response = compute.instances().start(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, instance=instance_name).execute()
    if wait:
        response = wait_for_operation(response)
        wait_port_open(get_instance_ip(instance_name), 22)

    log.info("Starting instance {} is successful".format(instance_name))
    return response

def stop_instance(instance_name, wait=False):
    log.info("Stopping instance {}".format(instance_name))
    
    try:
        response = compute.instances().stop(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, instance=instance_name).execute()
        if wait:
            response = wait_for_operation(response)

        log.info("Stopping instance {} is successful".format(instance_name))
        return response
    except HttpError as e:
        log.warn("Instance {} was not found".format(instance_name))
        if e.args[0]['status'] != '404':
            raise e

def delete_instance(instance_name, wait=False):
    log.info("Deleting instance {}".format(instance_name))

    try:
        response = compute.instances().delete(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, instance=instance_name).execute()
        if wait:
            response = wait_for_operation(response)

        log.info("Deleting instance {} is successful".format(instance_name))
        return response
    except HttpError as e:
        log.warn("Instance {} was not found".format(instance_name))
        if e.args[0]['status'] != '404':
            raise e

def wait_port_open(ip, port):
    log.info("Waiting for {}:{} to open".format(ip, port))
    for _ in range(150):    # 2.5 minutes
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            log.info("Port is open")
            return
        except:
            time.sleep(1)
            pass
    log.error("Timeout while waiting for {}:{} to open".format(ip, port))

def list_instances():
    log.info("Listing instances")
    response = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()

    instances = {}
    for instance in response['items']:
        instances[instance['name']] = {
                'type': instance['labels']['type'] if 'labels' in instance else '', 
                'status': instance['status'] if 'status' in instance else '', 
                'ip': instance['networkInterfaces'][0]['accessConfigs'][0]['natIP'] if instance['status'] == 'RUNNING' else ''
            }
    
    log.info(str(instance))
    return instances

def get_instance_ip(instance_name):
    log.info("Getting ip for instance {}".format(instance_name))
    result = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
    if 'items' not in result:
        log.error("No instances found")
        return None

    for instance in result['items']:
        if instance['selfLink'].split('/')[-1] == instance_name and instance['status'] == 'RUNNING':
            ip = instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']
            log.info("IP of instance {} is {}".format(instance_name, ip))
            return ip

    log.error("Instance {} was not found".format(instance_name))
    return None


def wait_for_operation(operation):
    log.info("Waiting for operation")
    
    itrs = 0
    while True:
        result = compute.zoneOperations().get(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, operation=operation['name']).execute()

        if result['status'] == 'DONE':
            log.info("Done{}".format(' ' * 10))
            if 'error' in result:
                raise Exception(result['error'])
            return result

        # print("{}{}{}".format(result['status'], '.' * itrs, ' ' * (3 - itrs)), end="\r")
        itrs = (itrs + 1) % 3

if __name__ == "__main__":
    print(list_instances())