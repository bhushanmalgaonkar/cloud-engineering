#!/usr/bin/python3

KV_STORE_HOST = 'localhost'
KV_STORE_PORT = 7894
KV_STORE_DB_PATH = 'kvstore.db'
KV_STORE_ROOT_DIR = 'chunks'
KV_STORE_BLOCK_SIZE = 1024 * 1024

MAP_REDUCE_MASTER_HOST = 'localhost'
MAP_REDUCE_MASTER_PORT = 9898

INTERMEDIATE_OUTPUTS_DIR = 'intermediate_outputs'

WORKERS = set([
    ('localhost', 1201)
])