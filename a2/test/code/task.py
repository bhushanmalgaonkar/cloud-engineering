def mapper(chunk):
    print('chunk: ', chunk)
    for ch in chunk.split():
        yield (ch, 1)