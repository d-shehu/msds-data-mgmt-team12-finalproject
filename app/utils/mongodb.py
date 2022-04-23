
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


def fnGetSearchString(searchText, searchMode):

    # For ANY just pass in as
    sModified = searchText
    # Match phrase exactly
    if (searchMode == utils.SearchMode.EXACT):
        # Strip quotes from the string since string is used to specify exact
        # Unfortunately this is a limitation
        sModified = searchText.replace("\"", "")
        sModified = "\"{0}\"".format(sModified)
    elif (searchMode == utils.SearchMode.ALL):
        # See comment above
        sModified = searchText.replace("\"", "")
        # tokenize
        lsTokenList = sModified.split()

        sModified = ""
        for sToken in lsTokenList:
            sModified = sModified + "\"{0}\" ".format(sToken)
    
    print("Info: modified search term: ", sModified)

    return sModified
    

def fnDisconnect(dbConnection):
    dbConnection.close()