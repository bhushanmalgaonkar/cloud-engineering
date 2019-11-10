def mapper(doc_id, chunk):
    for ch in chunk.split():
        yield (ch, 1)

def reducer(key_values):
    for key, value in key_values.items():
        yield (key, sum(value))