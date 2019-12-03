#!/bin/bash

zone='us-central1-c'

echo -e "***Deleting KeyValueStore"
gcloud compute instances delete key-value-store --zone $zone --quiet

echo -e "***\n\nDeleting MapReduceMaster"
gcloud compute instances delete map-reduce-master --zone $zone --quiet

echo -e "***\n\nDeleting base-snapshot"
