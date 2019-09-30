#!/bin/bash

find . -name "*.java" -print | xargs javac
java MemcacheServerLoadTest localhost 8888
