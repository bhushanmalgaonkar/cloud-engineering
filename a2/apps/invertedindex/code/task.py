def mapper(doc_id, chunk):
    for ch in chunk.split():
        yield (ch, doc_id)

def reducer(key_values):
    for key, value in key_values.items():
        yield (key, set(value))