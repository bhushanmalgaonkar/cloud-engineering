from datetime import datetime
from uuid import uuid4

from constants import KV_STORE_BLOCK_SIZE

'''
    Creates and returns random id that is very unlikely to occur twice
'''
def generateId():
    return '{}-{}'.format(uuid4(), datetime.now().strftime("%y%m%d-%H%M%S"))

'''
    Reads a file as text and returns an iterator of chunks each of size close to BLOCK_SIZE
'''
def file_iterator(filepath):
    # minimize rpc calls by send multiple lines in single rpc call
    # limit the total size of data < BLOCK_SIZE
    chunk_index = 0
    with open(filepath, 'r') as f:
        block = []
        block_size = 0
        while True:
            line = f.readline()
            if not line:
                break

            block.append(line)
            block_size += len(line)
            if block_size > KV_STORE_BLOCK_SIZE:
                yield (chunk_index, ''.join(block))
                block.clear()
                block_size = 0
                chunk_index += 1
        
        if block_size > 0:
            yield (chunk_index, ''.join(block))


def str_iterator(string):
    block = []
    block_size = 0
    chunk_index = 0
    for splt in string.split('\n'):
        line = splt + '\n'
        
        block.append(line)
        block_size += len(line)
        if block_size > KV_STORE_BLOCK_SIZE:
            yield (chunk_index, ''.join(block))
            block.clear()
            block_size = 0
            chunk_index += 1
        
    if block_size > 0:
        yield (chunk_index, ''.join(block))