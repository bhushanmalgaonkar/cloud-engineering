import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

GCLOUD_PROJECT = 'bhushan-malgaonkar'
GCLOUD_REGION = 'us-central1'
GCLOUD_ZONE = 'us-central1-c'

compute = build('compute', 'v1')

def create_worker_boot_disk(disk_name, wait=False):
    print("Creating worker boot disk {}".format(disk_name))

    disk_body = {
        "name": disk_name,
        "sourceSnapshot": "projects/{}/global/snapshots/test-image".format(GCLOUD_PROJECT),
        "sizeGb": "10",
        "type": "projects/{}/zones/{}/diskTypes/pd-standard".format(GCLOUD_PROJECT, GCLOUD_ZONE),
        "zone": "projects/{}/zones/{}".format(GCLOUD_PROJECT, GCLOUD_ZONE)
    }

    response = compute.disks().insert(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, body=disk_body).execute()
    if wait:
        return wait_for_operation(response)
    return response

def delete_disk(disk_name, wait=False):
    print("Deleting disk {}".format(disk_name))

    response = compute.disks().delete(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, disk=disk_name).execute()
    if wait:
        return wait_for_operation(response)
    return response

def create_worker_instance(instance_name, disk_name=None, wait=False):
    print("Creating worker instance {}".format(disk_name))

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
            "subnetwork": "projects/{}/regions/{}/subnetworks/default".format(GCLOUD_PROJECT, GCLOUD_REGION,
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
                    "https://www.googleapis.com/auth/trace.append"
                ]
            }
        ]
    }
    response = compute.instances().insert(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, body=instance_body).execute()
    if wait:
        return wait_for_operation(response)
    return response

def start_instance(instance_name, wait=False):
    print("Stopping instance {}".format(instance_name))

    response = compute.instances().start(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, instance=instance_name).execute()
    if wait:
        return wait_for_operation(response)
    return response

def stop_instance(instance_name, wait=False):
    print("Stopping instance {}".format(instance_name))
    
    try:
        response = compute.instances().stop(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, instance=instance_name).execute()
        if wait:
            return wait_for_operation(response)
        return response
    except HttpError as e:
        if e.args[0]['status'] != '404':
            raise e

def delete_instance(instance_name, wait=False):
    print("Deleting instance {}".format(instance_name))

    try:
        response = compute.instances().delete(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, instance=instance_name).execute()
        if wait:
            return wait_for_operation(response)
        return response
    except HttpError as e:
        if e.args[0]['status'] != '404':
            raise e

from pprint import pprint
def get_instance_ip(instance_name):
    result = compute.instances().list(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE).execute()
    if 'items' not in result:
        return None

    for instance in result['items']:
        if instance['selfLink'].split('/')[-1] == instance_name and instance['status'] == 'RUNNING':
            return instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']

    return None


def wait_for_operation(operation):
    print("Waiting for operation")
    
    itrs = 0
    while True:
        result = compute.zoneOperations().get(project=GCLOUD_PROJECT, zone=GCLOUD_ZONE, operation=operation['name']).execute()

        if result['status'] == 'DONE':
            print("Done{}".format(' ' * 10))
            if 'error' in result:
                raise Exception(result['error'])
            return result

        print("{}{}{}".format(result['status'], '.' * itrs, ' ' * (3 - itrs)), end="\r")
        itrs = (itrs + 1) % 3

        time.sleep(1)