#!/usr/bin/python3

KV_STORE_HOST = 'localhost'
KV_STORE_PORT = 7894
KV_STORE_DB_PATH = 'kvstore.db'
KV_STORE_ROOT_DIR = 'chunks'
KV_STORE_BLOCK_SIZE = 1024 * 1024
KV_STORE_ENCODING = 'utf-8'

MAP_REDUCE_MASTER_HOST = 'localhost'
MAP_REDUCE_MASTER_PORT = 9898

INTERMEDIATE_OUTPUTS_DIR = 'intermediate_outputs'

WORKERS = list(set([
    ('localhost', 1200),
    ('localhost', 1201),
    ('localhost', 1202),
    ('localhost', 1203)
]))
TASKS_PER_WORKER = 2
