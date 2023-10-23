import urllib3
import json
import random
import string
import urllib.parse
import os
import ydb
import ydb.iam

# Для базы данных 
driver_config = ydb.DriverConfig(
    endpoint=os.getenv('YDB_ENDPOINT'), 
    database=os.getenv('YDB_DATABASE'),
    credentials=ydb.iam.MetadataUrlCredentials()
)

driver = ydb.Driver(driver_config)
driver.wait(fail_fast=True, timeout=5)
pool = ydb.SessionPool(driver)

def randomword(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def insert_artists(tablename, artist):
    # create the transaction and execute query.
    text = f"INSERT INTO {tablename} SELECT '{randomword()}' as id, '{artist}' as name;"
    return pool.retry_operation_sync(lambda s: s.transaction().execute(
        text,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))

def insert_genres(tablename, genre_reply):
    # create the transaction and execute query.
    text = f"INSERT INTO {tablename} SELECT '{randomword()}' as id, '{genre_reply}' as genre_name;"
    return pool.retry_operation_sync(lambda s: s.transaction().execute(
        text,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))

def insert_similar(tablename, artist_name):
    # create the transaction and execute query.
    text = f"INSERT INTO {tablename} SELECT '{randomword()}' as id, '{artist_name}' as name;"
    return pool.retry_operation_sync(lambda s: s.transaction().execute(
        text,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))
