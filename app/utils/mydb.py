# Data stores
import os
from pymongo import MongoClient

def fnGetTweetDBName():
    return "tweetDB"

def fnGetTweetCollection():
    return "tweet"
    
def fnConnectToMongo():
   
    dbConnection = None
    try:
        # Connects to the default port for Mongo within the internal network
        dbConnection = MongoClient( host=os.getenv('MONGO_DB_HOSTNAME'),
                                    username=os.getenv('MONGO_DB_USERNAME'), 
                                    password=os.getenv('MONGO_DB_PASSWORD'))

        print("Connected to MongoDB successfully")
    except Exception as error:
        print("Error while trying to connect to Mongo")
    
    return dbConnection

# This drops the collection if it exists
def fnCreateTweetDB(dbConnection):
    try:
        if dbConnection != None:
            tweetDB = dbConnection[fnGetTweetDBName()]
            sTweetCollection = fnGetTweetCollection()
            # Drop if it exists so we start with a clean slate
            if sTweetCollection in tweetDB.list_collection_names():
                tweetDB[sTweetCollection].drop()

        return tweetDB[sTweetCollection]
    except Exception as error:
        print("Error while creating collection: ", error)

def fnGetAllTweets(dbConnection):
    lsTweets = []

    try:
        tweetDB = dbConnection[fnGetTweetDBName()]
        sTweetCollection = fnGetTweetCollection()

        lsTweets = list(tweetDB[sTweetCollection].find())
    except Exception as error:
        print("Unable to fetch tweets from Mongo: ", error)

    return lsTweets

def fnDisconnectFromMongo(dbConnection):
    dbConnection.close()