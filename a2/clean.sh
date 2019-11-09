#!/bin/bash

rm -f kvstore.db
rm -rf chunks save_path intermediate_outputs
find . -name __pycache__ | xargs rm -rf
