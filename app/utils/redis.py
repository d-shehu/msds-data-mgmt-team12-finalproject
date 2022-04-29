import redis
import os

# Redis maintains a connection pool so no need to close connection explicitly
def fnConnect(maxSearchResults, expiryTime):

    redisData = {"connRedis": None, "maxSearchResults": maxSearchResults, "expiryTime": expiryTime}
    print("Redis settings:", redisData)
    try:
        redisData["connRedis"] = redis.Redis(host=os.getenv('REDIS_DB_HOSTNAME'), 
                                password=os.getenv('REDIS_DB_PASSWORD'),
                                db=1)

    except Exception as e:
        print("Error: could not connect to Redis:", e)

    return redisData

def fnCacheSearchResults(redisData, searchCriteria, lsResults):
    try:
        
        connRedis = redisData["connRedis"]
        maxSearchResults = redisData["maxSearchResults"]
        expiryTime = redisData["expiryTime"]

        # If there are too many search results in cache check
        # to see if they were expired by Redis. If not remove
        # them to free up a slot.
        while connRedis.llen("cachedResults") >= maxSearchResults:
            searchKey = connRedis.lpop("cachedResults")
            # It's possible Redis expired. Don't have a handler
            # to respond to expire so just pop it from this list
            if connRedis.exists(searchKey):
                print("Removing item from cache")
                connRedis.delete()

        connRedis.set(searchCriteria, lsResults, expiryTime)
        connRedis.lpush("cachedResults", searchCriteria)

    except Exception as e:
        print("Error: could not store search results in cache")

def fnFetchSearchResults(redisData, searchCriteria):
    lsResults = None
    try:
        connRedis = redisData["connRedis"]
        if connRedis.exists(searchCriteria):
            res = connRedis.get(searchCriteria)
            lsResults = res.decode()
        
    except Exception as e:
        print("Error: could not fetch search results from cache")
    
    return lsResults
