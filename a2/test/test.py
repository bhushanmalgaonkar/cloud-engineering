#!/usr/bin/python3

import os
import sys

sys.path.insert(1, './code')
task = __import__('task')
print(task)

for ch in task.mapper('hello world'):
    print(ch)