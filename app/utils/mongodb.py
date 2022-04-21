
import os
from pymongo import MongoClient

def fnConnect():
   
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
        
        fnDisconnect(dbConnection)
    except Exception as error:
        print("Error while creating collection: ", error)

def fnGetCollections(dbConnection):
    try:
        tweetDB = dbConnection[fnGetTweetDBName()]
        return tweetDB[fnGetTweetCollection()], tweetDB[fnGetTagCollection()]
    except Exception as error:
        print("Error while creating collection: ", error)

def fnDisconnect(dbConnection):
    dbConnection.close()