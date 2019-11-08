#!/usr/bin/python3
import argparse

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 12345

def submit_job(host, port, dir, code):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MapReduce Client")
    parser.add_argument('-h', '--host', type=str, default='localhost',
                        help='host to connect to')
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                        help='listen on/connect to port <port> (default={}'
                        .format(DEFAULT_PORT))
    parser.add_argument('-d', '--input-directory', type=str,
                        help='directory which contains all the input files')
    parser.add_argument('-c', '--code', type=str,
                        help='code file')

    args = parser.parse_args()
    submit_job(args['host'], args['port'], args['file'], args['code'])