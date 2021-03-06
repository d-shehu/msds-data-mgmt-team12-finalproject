
from ctypes import util
from dataclasses import replace
import os
import pymongo

from . import utils

def fnConnect():
   
    dbConnection = None
    try:
        # Connects to the default port for Mongo within the internal network
        dbConnection = pymongo.MongoClient( host=os.getenv('MONGO_DB_HOSTNAME'),
                                    username=os.getenv('MONGO_DB_USERNAME'), 
                                    password=os.getenv('MONGO_DB_PASSWORD'))

        print("Connected to MongoDB successfully")
    except Exception as error:
        print("Error while trying to connect to Mongo")
    
    return dbConnection

def fnGetTweetDBName():
    return "tweetDB"

def fnGetTweetCollection():
    return "tweet"

# This drops the collection if it exists
def fnInitDB():
    try:
        dbConnection = fnConnect()

        tweetDB = dbConnection[fnGetTweetDBName()]
        # Clear the collections assuming they exist. Otherwise they get
        # created the next time we grab them
        tweetDB.drop_collection(fnGetTweetCollection())

        # Create some obvious indexes
        tweetDB[fnGetTweetCollection()].create_index("tweet_id")
        tweetDB[fnGetTweetCollection()].create_index("creator_id")
        tweetDB[fnGetTweetCollection()].create_index("tags")
        tweetDB[fnGetTweetCollection()].create_index("user_mentions")
        tweetDB[fnGetTweetCollection()].create_index([('text', 'text')])

        # Create index in descending order as results sorted from most recent
        tweetDB[fnGetTweetCollection()].create_index([('created_at', pymongo.DESCENDING)])
        tweetDB[fnGetTweetCollection()].create_index([('retweet_count', pymongo.DESCENDING)])
        tweetDB[fnGetTweetCollection()].create_index([('favorite_count', pymongo.DESCENDING)])
        tweetDB[fnGetTweetCollection()].create_index([('quote_count', pymongo.DESCENDING)])
        tweetDB[fnGetTweetCollection()].create_index([('creator_influence', pymongo.DESCENDING)])

        fnDisconnect(dbConnection)
    except Exception as error:
        print("Error while creating collection: ", error)

def fnGetCollections(dbConnection):
    try:
        tweetDB = dbConnection[fnGetTweetDBName()]
        return tweetDB[fnGetTweetCollection()]
    except Exception as error:
        print("Error while creating collection: ", error)

def fnSearchText(searchCriteria, sField, sSearchText):
    searchCriteria[("$" + sField)] = { "$search": sSearchText }

# Search for tags with the 3 modes given. Similar to the text search
# but syntax is a bit different.
# See: https://www.mongodb.com/docs/manual/tutorial/query-arrays/
def fnSearchTags(searchCriteria, sField, lsTags, searchMode):
    # All tags in this order
    if searchMode == utils.SearchMode.EXACT:
        searchCriteria[sField] = lsTags
    # Every tags but in any order in text
    elif searchMode == utils.SearchMode.ALL:
        searchCriteria[sField] = { "$all": lsTags }
    elif searchMode == utils.SearchMode.ANY:
        searchCriteria[sField] = { "$in": lsTags }
    else:
        print("Error: unknown search mode:", searchMode)

# TODO: the Mongo code shouldn't know about the format of the data
# Ideally this can be pushed to the tweet class and/or otherwise
# refactored.
def fnSearchPeople(searchCriteria, lsPeople, searchMode):
    # All tags in this order
    # Must be an ID
    if searchMode == utils.PeopleSearchMode.FROM:
        searchCriteria["creator_id"] = { "$in": lsPeople }
    # Every tags but in any order in text
    # Must be an ID
    elif searchMode == utils.PeopleSearchMode.REPLY:
        searchCriteria["reply_to_user_id"] = { "$in": lsPeople }
    # Should be text
    elif searchMode == utils.PeopleSearchMode.MENTION:
        searchCriteria["user_mentions"] = { "$in": lsPeople }
    else:
        print("Error: unknown search mode:", searchMode)

def fnSearchRange(searchCriteria, sField, sStart, sEnd):
    searchCriteria[sField] = { "$lt": sEnd, "$gte": sStart }

def fnSearchExactValue(searchCriteria, sField, sValue):
    searchCriteria[sField] = { "$eq": sValue }

def fnSearchIn(searchCriteria, sField, lsValues):
    searchCriteria[sField] = { "$in": lsValues }

def fnApplyDisplayOrder(tweetResults, displayOrder):

    ret = tweetResults

    if displayOrder == utils.DisplayOrder.LATEST:
        tweetResults = tweetResults.sort([("created_at", pymongo.DESCENDING)])

    elif displayOrder == utils.DisplayOrder.POPULAR:
        # Note: might be interesting to sort by composite of retweet, favorite
        tweetResults = tweetResults.sort([("retweet_count", pymongo.DESCENDING)])
        
    elif displayOrder == utils.DisplayOrder.AUTHORITATIVE:
        # Note: this could also be on how authoritative the creator is
        tweetResults = tweetResults.sort([("quote_count", pymongo.DESCENDING)])

    elif displayOrder == utils.DisplayOrder.INFLUENCE:
        # Using an approximation of influence to provide an alternate view of tweets
        tweetResults = tweetResults.sort([("creator_influence", pymongo.DESCENDING)])
    
    else:
        print("Error: unexpected display order", displayOrder)

    return ret

def fnDisconnect(dbConnection):
    dbConnection.close()