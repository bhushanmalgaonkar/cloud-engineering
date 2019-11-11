#!/usr/bin/python3

from multiprocessing import Process

from kvstore_server import run_kvstore_server
from mapreduce_master import run_mapreduce_master
from mapreduce_worker import run_mapreduce_worker

from constants import WORKERS

if __name__ == '__main__':
    try:
        kvstore = Process(target=run_kvstore_server, args=())
        kvstore.start()

        mapreduce_master = Process(target=run_mapreduce_master, args=())
        mapreduce_master.start()

        mapreduce_workers = []
        for worker in WORKERS:
            host, port = worker
            mrw = Process(target=run_mapreduce_worker, args=(port, ))
            mrw.start()
            mapreduce_workers.append(mrw)

        kvstore.join()
        mapreduce_master.join()
        for worker in mapreduce_workers:
            worker.join()

        print('all set up!')
    except KeyboardInterrupt:
        print('shutting down.')
        if kvstore:
            kvstore.terminate()
        if mapreduce_master:
            mapreduce_master.terminate()
        if mapreduce_workers:
            for worker in mapreduce_workers:
                worker.terminate()
            