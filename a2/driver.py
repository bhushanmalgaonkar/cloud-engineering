#!/usr/bin/python3

def do():
    print(5)

import pickle

ser = pickle.dumps(do)


ret = pickle.loads(ser)
ret()
