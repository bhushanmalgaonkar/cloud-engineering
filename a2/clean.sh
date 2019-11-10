#!/bin/bash

rm -f kvstore.db
rm -rf chunks save_path intermediate_outputs logs
find . -name __pycache__ | xargs rm -rf
