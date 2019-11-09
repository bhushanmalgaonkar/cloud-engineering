

## SQL tables
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


## Design decisions
1. **Upload input files and code file in key-value store as chunks and let workers pick it from there instead of directly passing the chunk using gRPC**
    1. The data stored in the key-value store gets a unique id that represents the entire data, be it a single file or multi-level directory. So once the data is uploaded, executing map-reduce is done simply by passing code_id and data_id. Master will only query the database to find all the chunk_ids associated with data_id and pass chunk_id and code_id to the worker, avoiding the master to read and chunk the data again. The code_id and data_id are independent, so it’s easy to execute any map-reduce code on any uploaded data.
    2. To allow fault tolerance, the master has to keep track of all the chunks currently executing on workers, to re-execute in case the worker fails. If we don’t store the data in the key-value store, we’ll have to keep it in the memory, which becomes increasingly infeasible as we scale. (Consider 1000s of mapper with operating on 1GB data)
