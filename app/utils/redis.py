import json
from bson import json_util

import redis
import os

from . import utils

# Redis maintains a connection pool so no need to close connection explicitly
def fnConnect():

    connRedis = None

    try:
        connRedis = redis.StrictRedis(host=os.getenv('REDIS_DB_HOSTNAME'), 
                                password=os.getenv('REDIS_DB_PASSWORD'),
                                db=1, charset="utf-8", decode_responses=True)

    except Exception as e:
        print("Error: could not connect to Redis:", e)

    return connRedis

def fnGetRedisData(searchCacheEnabled, maxSearchResults, expiryTime, 
                        displayOrder, maxResults, simpleSearch):

    connRedis = fnConnect()

    redisData = {"connRedis": connRedis, "searchCacheEnabled": searchCacheEnabled,
                    "maxSearchResults": maxSearchResults, "expiryTime": expiryTime,
                    "displayOrder": displayOrder, "maxResults": maxResults,
                    "simpleSearch": simpleSearch}

    print("Redis settings:", redisData)

    return redisData

def fnCacheSearchResults(redisData, searchCriteria, jsonResults):
    try:
        
        connRedis = redisData["connRedis"]
        maxSearchResults = int(redisData["maxSearchResults"])
        expiryTime = int(redisData["expiryTime"])

        # If there are too many search results in cache check
        # to see if they were expired by Redis. If not remove
        # them to free up a slot.
        print("Num results cached:", connRedis.llen("cachedResults"))
        while connRedis.llen("cachedResults") >= maxSearchResults:
            searchKey = connRedis.lpop("cachedResults")
            # It's possible Redis expired. Don't have a handler
            # to respond to expire so just pop it from this list
            if connRedis.exists(searchKey):
                print("Removing item from cache")
                connRedis.delete(searchKey)

        connRedis.set(searchCriteria, jsonResults, expiryTime)
        connRedis.lpush("cachedResults", searchCriteria)

    except Exception as e:
        print("Error: could not store search results in cache", e)

def fnFetchRankResults(redisData):
    ret = None
    try:
        connRedis = redisData["connRedis"]
        simpleSearch = redisData["simpleSearch"]

        # Let's check the sorted set to see if these are simple search
        if simpleSearch:
            maxResults = redisData["maxResults"]
            displayOrder = utils.fnGetDisplayOrder(redisData["displayOrder"])

            print("Fetching simple cached search results: ", displayOrder)
            # OK simple searches corresponding to leaderboards (sorted set)
        
            if displayOrder == utils.DisplayOrder.LATEST:
                lsResults = fnGetReverseRank(connRedis, "created_at", maxResults)
            elif displayOrder == utils.DisplayOrder.POPULAR:
                lsResults = fnGetReverseRank(connRedis, "retweet_count", maxResults)
            elif displayOrder == utils.DisplayOrder.AUTHORITATIVE:
                lsResults = fnGetReverseRank(connRedis, "quote_count", maxResults)
            elif displayOrder == utils.DisplayOrder.INFLUENCE:
                lsResults = fnGetReverseRank(connRedis, "creator_influence", maxResults)
            else:
                print("Error: could not fetch ranked results, unknown display order", displayOrder)
            #print("Cached results:", lsResults)
            ret = lsResults
            #print(ret)
        
    except Exception as e:
        print("Error: could not fetch rank results from cache", e)
    
    return ret

def fnFetchSearchResults(redisData, searchCriteria):
    ret = None
    try:
        connRedis = redisData["connRedis"]
        if connRedis.exists(searchCriteria):
            ret = connRedis.get(searchCriteria)
        
    except Exception as e:
        print("Error: could not fetch search results from cache", e)
    
    return ret

# Assume we want to keep the highest scores
def fnAddRankedItem(connRedis, sSetName, rankVal, sItemVal, maxItems):
    try:
        #print(sSetName, rankVal)
        connRedis.zadd(sSetName, {sItemVal: rankVal})

        # Let's bound each cache (sorted set)
        if connRedis.zcard(sSetName) > maxItems:
           #print("Ranked: removing lowest score")
            connRedis.zpopmin(sSetName) # drop the lowest score

    except Exception as e:
        print("Error: could not add ranked items due to:", e)

def fnGetReverseRank(connRedis, sSetName, maxItems):

    lsResults = []

    try:
        lsResultsInCache = connRedis.zrevrange(sSetName, 0, maxItems)
        # TODO: cleanup serialization
        # Each item is a json object so convert to dictionary
        for item in lsResultsInCache:
            lsResults.append(json.loads(item))

    except Exception as e:
        print("Error: could not fetch ranked list due to:", e) 

    return lsResults
