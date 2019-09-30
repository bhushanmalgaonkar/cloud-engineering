#!/bin/bash

find . -name "*.java" -print | xargs javac
java MemcacheClient localhost 8888
