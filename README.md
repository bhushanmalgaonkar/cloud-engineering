## How to run
#### 1. Create a project using Google cloud console
  - Update following variables in gcloud_util.py
    - GCLOUD_PROJECT
    - GCLOUD_REGION
    - GCLOUD_ZONE
    
#### 2. Setup private key
  - Go to API & Service, Credentials, Create credentials, Service account key
  - Create a new service account with Compute Admin privileges
  - Select JSON key before creating the account. This will download the key to your machine
  - Create new environment variable GOOGLE_APPLICATION_CREDENTIALS to point to this key, e.g. in Linux
    - temporary: ```export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key```, or
    - permenant: ```echo 'export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key' >> ~/.profile && source ~/.profile```)
    
#### 3. Open ports in firewall
  - Go to VPC Network, Firewall rules and create following rules
  
| Name               | Priority | Direction of traffic | Action on match | Targets                      | Source filter | Source IP ranges | Protocol and ports |
|--------------------|----------|----------------------|-----------------|------------------------------|---------------|------------------|--------------------|
| allow-kvstore-7894 | 65534    | Ingress              | Allow           | All instances in the network | IP ranges     | 0.0.0.0/0        | tcp: 7894          |
| allow-master-9898  | 65534    | Ingress              | Allow           | All instances in the network | IP ranges     | 0.0.0.0/0        | tcp: 9898          |
| allow-mysql-3306   | 65534    | Ingress              | Allow           | All instances in the network | IP ranges     | 0.0.0.0/0        | tcp: 3306          |
| allow-worker-5000  | 65534    | Ingress              | Allow           | All instances in the network | IP ranges     | 0.0.0.0/0        | tcp: 5000          |
  
#### 3. Deploy
  - ```scripts/command.sh deploy```  
  - [logs](https://github.com/bhushanmalgaonkar/cloud-engineering/blob/master/scripts/logs/deploy.log)

#### 4. Run map-reduce task
  - ```python3 a2/mapreduce_client.py -d a2/apps/invertedindex/data -c a2/invertedindex/code -o a2/invertedindex/result```
  - [client.log](https://github.com/bhushanmalgaonkar/cloud-engineering/blob/master/scripts/logs/invertedindex-logs/client.log)
  - [server.log](https://github.com/bhushanmalgaonkar/cloud-engineering/blob/master/scripts/logs/invertedindex-logs/master-9898.log)

## Time taken by different operations
#### 1. Deploy: 7m48.408s
#### 2. Delete (cleaning up): 2m48.234s
#### 3. Create workers
  - 1 workers, 1m41s
  - 2 workers, 1m39s
  - 3 workers, 1m43s
  - 4 workers, 1m42s
#### 4. Inverted-index
  - 2 workers, 1 tasks/worker: 3m36.292s
  - 2 workers, 2 tasks/worker: 3m31.292s
  - 4 workers, 1 tasks/worker: 3m31.604s
  - 4 workers, 2 tasks/worker: 3m28.292s
  - 6 workers, 1 tasks/worker: 3m25.342s
  - 6 workers, 2 tasks/worker: 3m21.342s

## Submiting a job
mapreduce_cilent.py provides command line api to submit a job to MapReduceMaster. Provide following arguments

    -d DATA, --data DATA            (directory which contains all the input files)
    -c CODE, --code CODE            (directory which contains code file)
    -o OUTPUT, --output OUTPUT      (directory where final output will be stored)

### -c CODE
The worker nodes expect code to be presented in certain format. The directory specified with -c option should contain single file `task.py` which should contain two methods
1. ```def mapper(doc_id, chunk)```: doc_id will contain the filename and chunk will contain actual data
2. ```def reducer(key_values)```: key_values will contain a dictionary with grouped mapper outputs

Example: code for inverted index
```
import os

def mapper(doc_id, chunk):
    doc_id = os.path.basename(doc_id)
    for ch in chunk.split():
        yield (ch, doc_id)

def reducer(key_values):
    for key, value in key_values.items():
        yield (key, set(value))
```

### run as
```./mapreduce_client.py -d data_directory -c code_directory -o output_directory```

## MapReduce
### MapReduceClient
The client reads the data and code from user system and stores it into key-value store. It then passes ids representing code and data to master

### MapReduceMaster
Collects ids of all the chunks (not actual data) associated with provided data_id, and schedules execution of each chunk on available workers. It also co-ordinates with workers on where to store intermediate output, so later it can shuffle/sort and schedule reducer execution. 

### MapReduceWorker
A worker is invoked by master to process single chunk of data. The worker gets the id of data and code. It downloads both using KeyValueStoreClient. A worker process can accept multiple simultaneous jobs and execute then in different threads. This limit is specified in constants.TASKS_PER_WORKER

## Key-Value store
### KeyValueStoreServer
Provides two gRPC methods.
    1. Save(key, value)
    2. Get(key)
    
The values are stored on local disk with key as filename and value as data. Files are saved as binary. Saving files as binary allows storing pickle dumps which is used for storing intermediate mapper outputs since the outputs can be of any type. If stored as text, it is not possible to determine the datatype of key and value while recovering mapper output.

### KeyValueStoreClient
Provides methods to store/retrieve files/directories in key-value store. It reads and divides the files into chunks of fixed size (constants.BLOCK_SIZE), assigns each chunk an unique id and saves it the KeyValueStore. 

Since KeyValueStore is minimal and doesn't provide any notion of files and directories, the KeyValueStoreClient maps an hierarchy of keys to unique id of the chunk. It saves the mapping in the database for efficient lookup. See **chunks** table below.

## GCP
### gcloud_util
Provides elementary funcationality to manipulate GCP compute resources such as create/delete/list worker instances, finding IP given instance name.

### ResourceManager
Provides higher level functionality to operate with GCP compute resources such as create/delete multiple instances, finding IP address of KeyValueStore and MapReduceMaster servers

### Instance configuration
All (master, worker, key-value-store) are launched on GCP n1-standard-1 (1 vCPU, 3.75GB memory) with following tweaks
```
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
"serviceAccounts": [
    {
        ...,
        "scopes": [
            ...,
            "https://www.googleapis.com/auth/compute"
        ]
    }
]
```

### Cost of developing/experimenting
$3.10

### GCP APIs
gcloud_util.py contains utilities to create/delete instances/disks, start/stop/list available instances, get IP of an instance given name.

## Database
1. **chunks**: stores location of a specific chunk of a file on the server

    |    dir_id     | doc_id        | chunk_index   | chunk_id      |
    | ------------- | ------------- | ------------- | ------------- |
    | The parameter used to link a set of files together. A function can be run on this set of files by simply passing dir_id to master  | The relative path of each file. This is the path present on the client machine  | If the file is greater than BLOCK_SIZE, it is divided into  | Path where the chunk is stored on the key-value server  |
    
2. **executions**: stores execution information of each individual worker task (map/reduce)

    |    exec_id    | exec_type     | chunk_id      | status        | result_doc_id |
    | ------------- | ------------- | ------------- | ------------- | ------------- |
    | Each execution gets unique id that client can use to track progress | map / reduce | Id of the chunk on which operation is being performed | pending / success / failure | location on the key-value server where result of the operation is stored. output of a worker is stored as single document under exec_id directory |
    
3. **jobs**: stores execution information of each job submitted to master

    |   exec_id     | code_id       | dir_id        | status        | result_dir_id |
    | ------------- | ------------- | ------------- | ------------- | ------------- |
    | Each execution gets unique id that client can use to track progress | code_id used for execution | dir_id used for execution | pending / success / failure | location on the key-value server where result of reduce operation is stored |

sqlalchemy uses connection pooling to allow concurrent access. However in case of sqlite3 (used for demo), as it doesn't support concurrent access, sqlachemy will allow on one connection to write to database at a time, as long as all the connection originate from same process. To achieve concurrency in multiprocess setup, we can use a database that supports concurrency e.g. MySQL. Because of sqlalchemy no changes are required when switching databases.

## Design decisions
1. **Upload input files and code file in key-value store as chunks and let workers pick it from there instead of directly passing the chunk using gRPC**
    1. The data stored in the key-value store gets a unique id that represents the entire data, be it a single file or multi-level directory. So once the data is uploaded, executing map-reduce is done simply by passing code_id and data_id. Master will only query the database to find all the chunk_ids associated with data_id and pass chunk_id and code_id to the worker, avoiding the master to read and chunk the data again. The code_id and data_id are independent, so it’s easy to execute any map-reduce code on any uploaded data.
    2. To allow fault tolerance, the master has to keep track of all the chunks currently executing on workers, to re-execute in case the worker fails. If we don’t store the data in the key-value store, we’ll have to keep it in the memory, which becomes increasingly infeasible as we scale. (Consider 1000s of mapper with operating on 1GB data)
    3. The overhead of reading and dividing input files into chunks is moved from Master to Client

2. **Manually starting worker processes instead of letting Master spawn them**
    1. Although the assignment says master should spawn all the mapper and reducer tasks, in reality these tasks will be run on different nodes where master will have no control over spawning new processes. Unless, we keep an agent on these nodes and register these nodes with master, then master can request nodes to spawn processes as required. Such an agent is implement in 'mapreduce_worker.py'
    
3. **Client should not have control over number of workers**
    1. Number of workers to be launched should be decided by master instead of client. Although not done in this assignment master can be made intelligent to detect load and launch more instances as required.
