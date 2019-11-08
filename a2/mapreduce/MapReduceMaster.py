#!/usr/bin/python3
import argparse

DEFAULT_PORT = 12345

def run_master():
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MapReduce")
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                        help='listen on/connect to port <port> (default={}'
                        .format(DEFAULT_PORT))
    parser.add_argument('-f', '--file', type=str,
                        help='input file')
    parser.add_argument('-c', '--code', type=str,
                        help='code file')

    args = parser.parse_args()

    run_master(args)