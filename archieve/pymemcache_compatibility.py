#!/usr/bin/python3

from pymemcache.client.base import Client

client = Client(('localhost', 8888))
client.set('some_key', 'some_value')
result = client.get('some_key')
print(result)
