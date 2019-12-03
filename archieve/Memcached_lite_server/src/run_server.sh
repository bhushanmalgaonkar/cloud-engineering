#!/bin/bash

find . -name "*.java" -print | xargs javac
java Server 8888
