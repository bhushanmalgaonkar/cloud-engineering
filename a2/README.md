## How to run locally
1. Open constants.py. Modify ports, add/remove workers. Save.
2. run ```./driver.py```. This is a utility that will parse constants.py and spwan kvstore, master and all the workers on current machine.

## How to run in distributed setup
1. Start worker processes on worker nodes. Update WORKERS in constants.py at master to point to these nodes ```./mapreduce_worker.py -p <port>```
2. Start key-value store. Update KV_STORE_* values in constants.py at master ```./kvstore_server.py```
3. Start MapReduceMaster ```./mapreduce_master.py```

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
