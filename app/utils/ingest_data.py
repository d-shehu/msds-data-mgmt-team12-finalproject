# This file is responsible for ingesting data into the data stores.
# It simulates streaming data by fetching 1 record at a time
# from the data stream, i.e. a file, and then parses it and inserts
# it into the appropriate database.

# System
from ntpath import join
import os
import json
from datetime import datetime

# User library imports
from . import redis
from . import tweet
from . import pgdb
from . import mongodb

def fnGetDataDir():
    return os.path.join("/", "data")

# Some schema and data needs to be pre-set after the app launches
# This is a wrapper for that
def fnInitSchemaData():
    dbConnection = pgdb.fnConnect()
    # Configure Postgres schema
    pgdb.fnInitSchema(dbConnection)
    # TODO: ;oad country and language meta data
    pgdb.fnDisconnect(dbConnection)

    mongodb.fnInitDB()

# Assuming the file has 1 JSON object per line, this function
# reads the line and returns the corresponding JSON.
def fnGetRecordFromJSON(sLine):
    data = None
    try:
        data = json.loads(sLine)
    except Exception as e:
        print("Parsing error:", e)
    
    return data

# Somewhat generalized reader function that iterates over all the records, or a subset, sample
# and then calls the process function to do something useful. 
def fnGetRecords(filepath, fnProcessRecord, iFrom=None, iTo=None, bVerbose=False, userData=None):
    
    iRecord = 0
    iPos = 0

    # Read JSON sample data with tweats
    try:
        print("Reading from ", filepath)

        fileSize = os.stat(filepath).st_size
        print("File is of size: ", fileSize)

        with open(filepath, "r") as sampleFile:

            # Lets get it one line at a time to avoid loading everything into memory
            for sLine in sampleFile:
                # Check control
                if ("continue" in userData and not userData["continue"] ):
                    break

                # Estimate progress. This is not super efficient
                # so will only call every so often
                iPos = iPos + len(sLine)
                if (iRecord % 100 == 1 and "progress" in userData):
                    userData["progress"] = float(iPos) / fileSize

                # Ignore whitespaces
                if not sLine.isspace():
                    # Limit to a range
                    if not iFrom is None and iRecord < iFrom:
                        iRecord = iRecord + 1
                        continue
                    if not iTo is None and iRecord >= iTo:
                        break
                    
                    if bVerbose:
                        print("Record", iRecord, ":")
                    
                    record = fnGetRecordFromJSON(sLine)
                    # Got a data object
                    if not record is None:
                        fnProcessRecord(record, userData)
                                    
                    elif bVerbose:
                        print("Record is undefined or not parsed")
                    
                    # Keep track of all non empty lines being processed. Assume correspond to JSON
                    # top-level object
                    iRecord = iRecord + 1 

            # All done without errors?
            userData["progress"] = 1.0 
    except Exception as e:
        print("Error while reading JSON records from memory", e)
        
    return iRecord 

def fnReadThreaded(readerData):

    try:
        mongoConnection = mongodb.fnConnect()
        pgConnection = pgdb.fnConnect()
        redisConnection = redis.fnConnect()

        if pgConnection is not None and mongoConnection is not None:
            # Check the MongoDB connection by fetching server info
            #serverInfo = mongoConnection.server_info()
            #print (serverInfo)

            # Create the database and collection
            tweetCollection = mongodb.fnGetCollections(mongoConnection)

            # Poor man's objected-oriented (i.e. should use class here)
            readerData["mongoConn"] = mongoConnection 
            readerData["pgConn"] = pgConnection
            readerData["redisConn"] = redisConnection
            readerData["tweetCollection"] = tweetCollection

            inFilepath = readerData["inFilepath"] # A must
            
            # Loop over records in JSON file
            fnGetRecords(inFilepath, tweet.fnProcessTweets, None, None, False, readerData)

        # Clean up connections
        if mongoConnection is not None:
            mongodb.fnDisconnect(mongoConnection)
        if pgConnection is not None:
            pgdb.fnDisconnect(pgConnection)
        # Nothing to do for Redis (manages it's own conns)

    except Exception as error:
        # Need a thread safe way to output errors
        print("Error while reading/processing tweets: ",error)
    
    readerData["isIngesting"] = False

def fnClearData():
    try:
        mongodb.fnInitDB()
        pgdb.fnClearData()

    except Exception as error:
        print("Error while trying to reset databases")
        
def fnGetReaderData(sampleFilename, insertDelay):
    sampleDataFilepath = os.path.join(fnGetDataDir(), sampleFilename)
    print("Using file: ", sampleDataFilepath)

    # Poor man's objected-oriented (i.e. should use class here)
    userData = {
        "inFilepath": sampleDataFilepath,
        "delay": insertDelay, # Milliseconds. Careful. There is a limit to how precise sys clock is.
        "continue": True, # Adding a control variable here so we can cancel
        "processed": 0, # Records processed
        "progress": 0.0, # estimated progression. 1.0 == complete
        "isIngesting": False
    }

    return (userData)
