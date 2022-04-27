
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

def fnGetTagCollection():
    return "tag"

# This drops the collection if it exists
def fnInitDB():
    try:
        dbConnection = fnConnect()

        tweetDB = dbConnection[fnGetTweetDBName()]
        # Clear the collections assuming they exist. Otherwise they get
        # created the next time we grab them
        tweetDB[fnGetTweetCollection()].drop()
        tweetDB[fnGetTagCollection()].drop()

        # Create some obvious indexes
        tweetDB[fnGetTweetCollection()].create_index("tweet_id")
        tweetDB[fnGetTweetCollection()].create_index("creator_id")
        tweetDB[fnGetTweetCollection()].create_index("tags")
        tweetDB[fnGetTweetCollection()].create_index([('text', 'text')])

        # Create index in descending order as results sorted from most recent
        tweetDB[fnGetTweetCollection()].create_index([('created_at', pymongo.DESCENDING)])
        
        fnDisconnect(dbConnection)
    except Exception as error:
        print("Error while creating collection: ", error)

def fnGetCollections(dbConnection):
    try:
        tweetDB = dbConnection[fnGetTweetDBName()]
        return tweetDB[fnGetTweetCollection()], tweetDB[fnGetTagCollection()]
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

def fnDisconnect(dbConnection):
    dbConnection.close()