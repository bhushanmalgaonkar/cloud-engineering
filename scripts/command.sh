#!/bin/bash

zone="us-central1-c"
base_snapshot="base-snapshot"
user="mruser"
map_reduce_master="map-reduce-master"
key_value_store="key-value-store"
mysql_password="P@ssword123"
database_name="kvstore"


if [[ $1 == 'deploy' ]]; then
    echo -e "***Creating instance for MapReduceMaster"
    gcloud compute instances create $map_reduce_master --zone $zone --scopes https://www.googleapis.com/auth/compute 
    
    echo -e "\n\n***Wait for VM to open SSH port"
    map_reduce_master_ip=$(gcloud compute instances list | awk '/'$map_reduce_master'/ {print $5}')
    while true; do
        if nc -w 1 -z $map_reduce_master_ip 22; then
            echo -e "VM is ready!"
            break
        fi
        sleep 1
    done
    
    echo -e "\n\n***Transferring code to VM"
    gcloud compute scp --recurse ../a2/ $user@$map_reduce_master: --zone $zone
    
    echo -e "\n\n***Transfer keys to MapReduceMaster"
    gcloud compute scp $GOOGLE_APPLICATION_CREDENTIALS $user@$map_reduce_master:~/gcloud.json --zone $zone
    gcloud compute ssh $user@$map_reduce_master --command "echo \"export GOOGLE_APPLICATION_CREDENTIALS=~/gcloud.json\" >> ~/.profile; source ~/.profile" --zone $zone
    echo -e "\n\n***Installing python dependencies"
    gcloud compute ssh $user@$map_reduce_master --command "sudo apt -y install python3-pip;pip3 install -r ~/a2/requirements.txt" --zone $zone
    
    echo -e "\n\n***Stopping instance"
    gcloud compute instances stop $map_reduce_master --zone $zone
    
    echo -e "\n\n***Saving snapshot"
    gcloud compute disks snapshot $map_reduce_master --snapshot-names $base_snapshot --zone $zone
    
    echo -e "\n\n***Creating instance for KeyValueStore using snapshot"
    gcloud compute disks create $key_value_store --size "10" --source-snapshot $base_snapshot --type "pd-standard" --zone $zone
    
    gcloud beta compute instances create $key_value_store --disk=name=$key_value_store,device-name=$key_value_store,mode=rw,boot=yes,auto-delete=yes --zone $zone
    
    echo -e "\n\n***Wait for VM to open SSH port"
    key_value_store_ip=$(gcloud compute instances list | awk '/'$key_value_store'/ {print $5}')
    while true; do
        if nc -w 1 -z $key_value_store_ip 22; then
            echo -e "VM is ready!"
            break
        fi
        sleep 1
    done
    
    echo -e "\n\n***Installing mysql-server"
    gcloud compute ssh $user@$key_value_store --command "sudo apt-get -y install mysql-server" --zone $zone
    
    echo -e "\n\n***Enabling remote access"
    gcloud compute ssh $user@$key_value_store --command "sudo sed -i 's/^bind-address.*/# bind-address = 127.0.0.1/' /etc/mysql/mariadb.conf.d/50-server.cnf; sudo service mysqld restart" --zone $zone 
    
    echo -e "\n\n***Creating mysql database and granting priviledges"
    create_database="CREATE DATABASE ${database_name}"
    grant_privileges="GRANT ALL PRIVILEGES ON ${database_name}.* TO 'root'@'%' IDENTIFIED BY '${mysql_password}' WITH GRANT OPTION"
    flush_privileges="FLUSH PRIVILEGES"
    
    gcloud compute ssh $user@$key_value_store --command "sudo mysql -u root -e \"${create_database};${grant_privileges};${flush_privileges}\"" --zone $zone
    
    echo -e "\n\n***Starting KeyValueStore server"
    gcloud compute ssh $user@$key_value_store --command "python3 ~/a2/kvstore_server.py > kvstore_server_stdout &" --zone $zone
    
    echo -e "\n\n***Restarting MapReduceMaster VM"
    gcloud compute instances start $map_reduce_master --zone $zone
    
    echo -e "\n\n***Wait for VM to open SSH port"
    map_reduce_master_ip=$(gcloud compute instances list | awk '/'$map_reduce_master'/ {print $5}')
    while true; do
        if nc -w 1 -z $map_reduce_master_ip 22; then
            echo -e "VM is ready!"
            break
        fi
        sleep 1
    done
    
    echo -e "\n\n***Starting MapReduceMaster server"
    gcloud compute ssh $user@$map_reduce_master --command "python3 ~/a2/mapreduce_master.py > mapreduce_master_stdout &" --zone $zone 
    
    echo -e "\n\n***KeyValueStore ip ${key_value_store_ip}"
    echo -e "\n\n***MapReduceMaster ip ${map_reduce_master_ip}"
    
elif [[ $1 == 'start' ]]; then

    echo -e "***Starting KeyValueStore, MapReduceMaster VM"
    gcloud compute instances start $user@$key_value_store $user@$map_reduce_master --zone $zone

    echo -e "\n\n***Waiting for VMs to open SSH port"
    key_value_store_ip=$(gcloud compute instances list | awk '/'$key_value_store'/ {print $5}')
    while true; do
        if nc -w 1 -z $key_value_store_ip 22; then
            echo -e "KeyValueStore VM is ready!"
            break
        fi
        sleep 1
    done    
    
    map_reduce_master_ip=$(gcloud compute instances list | awk '/'$map_reduce_master'/ {print $5}')
    while true; do
        if nc -w 1 -z $map_reduce_master_ip 22; then
            echo -e "MapReduceMaster VM is ready!"
            break
        fi
        sleep 1
    done

    echo -e "\n\n***Starting KeyValueStore server"
    gcloud compute ssh $user@$key_value_store --command "python3 ~/a2/kvstore_server.py > kvstore_server_stdout &" --zone $zone
    
    echo -e "\n\n***Starting MapReduceMaster server"
    gcloud compute ssh $user@$map_reduce_master --command "sudo sed -i \"s/^KV_STORE_HOST.*/KV_STORE_HOST = \'${key_value_store_ip}\'/g\" ~/a2/constants.py; python3 ~/a2/mapreduce_master.py > mapreduce_master_stdout &" --zone $zone 
    
    echo -e "\n\n***KeyValueStore ip ${key_value_store_ip}"
    echo -e "\n\n***MapReduceMaster ip ${map_reduce_master_ip}"
elif [[ $1 == 'stop' ]]; then
    
    echo -e "***Stopping KeyValueStore, MapReduceMaster VM"
    gcloud compute instances stop $key_value_store $map_reduce_master --zone $zone

elif [[ $1 == 'delete' ]]; then

    echo -e "***Deleting KeyValueStore"
    gcloud compute instances delete key-value-store --zone $zone --quiet
    
    echo -e "***\n\nDeleting MapReduceMaster"
    gcloud compute instances delete map-reduce-master --zone $zone --quiet
    
    echo -e "***\n\nDeleting all MapReduceWorkers"
    gcloud compute instances list --filter="labels:map-reduce-worker" | awk 'NR>1 {print $1}' | xargs -L 1 gcloud compute instances delete --zone $zone --quiet

    echo -e "***\n\nDeleting base-snapshot"
    gcloud compute snapshots delete base-snapshot --quiet

else

    echo -e "Specify command deploy/start/stop/delete"

fi


