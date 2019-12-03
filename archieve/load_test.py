#!/usr/bin/python3

from pymemcache.client.base import Client

import random
import string
import threading
import time

max_active_threads = 0
active_threads = 0
lock = threading.Lock()

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def startClient(id):
    global active_threads
    global max_active_threads

    try:
        client = Client(('localhost', 8888))
        print('Client ' + str(id) + ' connected')
        start = time.time()

        lock.acquire()
        active_threads += 1
        max_active_threads = max(max_active_threads, active_threads)
        lock.release()

        for _ in range(500):
            key, value = randomString(5), randomString(5)
            client.set(key, value)
            result = client.get(key)

        lock.acquire()
        active_threads -= 1
        lock.release()

        end = time.time()
        print('Client ' + str(id) + ' exiting. Time spent: ' + str(end - start))
        end = time.time()
    except BaseException as e:
        print('Exception' + str(e))
        return

for i in range(500):
    t = threading.Thread(target=startClient, args=(i,))
    t.start()

while active_threads > 0:
    print('Active clients: ' + str(active_threads) + ', Max Active clients: ' + str(max_active_threads))
    time.sleep(1)
