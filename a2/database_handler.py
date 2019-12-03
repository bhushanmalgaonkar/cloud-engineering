#!/usr/bin/python3

import sqlalchemy as db
from sqlalchemy.pool import QueuePool

class DataBaseHandler:
    def __init__(self, path):
        self.engine = db.create_engine(path)
        conn = self.engine.connect()        
        conn.execute(""" CREATE TABLE IF NOT EXISTS chunks (
                        dir_id VARCHAR(50) NOT NULL,
                        doc_id VARCHAR(50) NOT NULL,
                        chunk_index int NOT NULL,
                        chunk_id VARCHAR(50) PRIMARY KEY
                    ); """)

        '''
            exec_type: map/reduce
            status: pending/success/failed

            stores execution status of individual mapper/reducer.
            it is updated by master when worker finishes. 
            used by master to 
                1. collect output of mappers to give to reducers
                2. collect output of reducer to answer user query
        '''
        conn.execute(""" CREATE TABLE IF NOT EXISTS executions (
                        exec_id VARCHAR(50) NOT NULL,
                        exec_type VARCHAR(50) NOT NULL,
                        chunk_id VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        result_dir_id VARCHAR(50)
                    ); """)

        '''
            stores execution status and result of entire map-reduce job
        '''
        conn.execute(""" CREATE TABLE IF NOT EXISTS jobs (
                        exec_id VARCHAR(50) NOT NULL,
                        code_id VARCHAR(50) NOT NULL,
                        dir_id VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        result_dir_id VARCHAR(50) NOT NULL
                    ); """)

        # metadata = db.MetaData()
        # self.chunks_table = db.Table('chunks', metadata, autoload=True, autoload_with=engine)
        # self.executions_table = db.Table('executions', metadata, autoload=True, autoload_with=engine)
        # self.jobs_table = db.Table('jobs', metadata, autoload=True, autoload_with=engine)

    def execute(self, sql, params):
        conn = self.engine.connect()
        trans = conn.begin()
        try:
            conn.execute(sql, params)
            trans.commit()
        except BaseException as e:
            print(e)
            trans.rollback()
        conn.close()

    def execute_and_return(self, sql, params):
        conn = self.engine.connect()
        rs = conn.execute(sql, params).fetchall()
        conn.close()
        return rs

    def save_chunk(self, dir_id, doc_id, chunk_index, chunk_id):
        self.execute(""" INSERT INTO chunks (dir_id, doc_id, chunk_index, chunk_id)
                                VALUES (%s, %s, %s, %s) """, (dir_id, doc_id, chunk_index, chunk_id))

    def get_chunk_metadata(self, dir_id, doc_id=None):
        if doc_id:
            rs = self.execute_and_return(""" SELECT dir_id, doc_id, chunk_index, chunk_id
                                FROM chunks
                                WHERE dir_id = %s AND doc_id = %s 
                                ORDER BY doc_id, chunk_index """, (dir_id, doc_id))
        else:
            rs = self.execute_and_return(""" SELECT dir_id, doc_id, chunk_index, chunk_id
                                FROM chunks
                                WHERE dir_id = %s
                                ORDER BY doc_id, chunk_index """, (dir_id))
        return rs

    def get_doc_metadata(self, dir_id):
        return self.execute_and_return(""" SELECT DISTINCT doc_id
                                FROM chunks
                                WHERE dir_id = %s """, (dir_id))


from constants import KV_STORE_DB_PATH
if __name__ == "__main__":
    db = DataBaseHandler(KV_STORE_DB_PATH)
    db.save_chunk('dir_id', 'doc_id', 0, 'chunk_id')
