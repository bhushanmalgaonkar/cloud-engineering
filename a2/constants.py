#!/usr/bin/python3

USER="mruser"

KV_STORE_PORT = 7894
MAP_REDUCE_MASTER_PORT = 9898
MAP_REDUCE_WORKER_PORT = 5000

KV_STORE_ROOT_DIR = 'chunks'
KV_STORE_BLOCK_SIZE = 1024 * 1024
KV_STORE_ENCODING = 'utf-8'

INTERMEDIATE_OUTPUTS_DIR = 'intermediate_outputs'

WORKERS = []
TASKS_PER_WORKER = 2
