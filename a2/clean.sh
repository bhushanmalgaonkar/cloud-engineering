#!/bin/bash

#rm -f kvstore.db
rm -f ./chunks/*
rm -rf save_path intermediate_outputs
find . -name __pycache__ | xargs rm -rf
