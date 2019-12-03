#!/bin/bash

zone='us-central1-c'

#echo 'Creating instance for kvstore'
#gcloud compute instances create kvstore --zone $zone 

#echo '10 sec sleep'
# sleep 10

echo 'Installing mysql-server'
gcloud compute ssh kvstore --zone $zone --command 'sudo apt-get install mysql-server'

echo 'Enabling remote access'
gcloud compute scp 50-server
#gcloud compute scp --recurse a2/ worker-1:

