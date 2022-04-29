import redis
import os

def fnConnect():

    connRedis = None
    try:
        connRedis = redis.Redis(host=os.getenv('REDIS_DB_HOSTNAME'), 
                                password=os.getenv('REDIS_DB_PASSWORD'),
                                db=1)

    except Exception as e:
        print("Error: could not connect to Redis:", e)

    return connRedis

def fnDisconnect(connRedis):

    try:
        connRedis.disconnect()
    except Exception as e:
        print("Error: could not disconnect from Redis", e)


def fnCacheSearches(connRedis, searchCriteria, lsResults):
    try:
        connRedis.set(searchCriteria, lsResults)
    except Exception as e:
        print("Error: could not store search results in cache")

def fnFetchSearch(connRedis, searchCriteria):
    lsResults = None
    try:
        res = connRedis.get(searchCriteria)
        if res is not None:
            lsResults = res.decode()
        
    except Exception as e:
        print("Error: could not fetch search results from cache")
    
    return 
