#!/usr/bin/python3

KV_STORE_HOST = '34.66.187.52'
KV_STORE_PORT = 7894
KV_STORE_DB_PATH = 'mysql+pymysql://root:P@ssword123@{}:3306/kvstore'.format(KV_STORE_HOST)
KV_STORE_ROOT_DIR = 'chunks'
KV_STORE_BLOCK_SIZE = 1024 * 1024
KV_STORE_ENCODING = 'utf-8'

MAP_REDUCE_MASTER_HOST = '35.202.18.136'
MAP_REDUCE_MASTER_PORT = 9898

INTERMEDIATE_OUTPUTS_DIR = 'intermediate_outputs'

WORKERS = list(set([
    ('localhost', 1200),
    ('localhost', 1201),
    ('localhost', 1202),
    ('localhost', 1203)
]))
TASKS_PER_WORKER = 2
