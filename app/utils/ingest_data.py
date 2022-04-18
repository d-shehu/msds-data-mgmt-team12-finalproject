# This file is responsible for ingesting data into the data stores.
# It simulates streaming data by fetching 1 record at a time
# from the data stream, i.e. a file, and then parses it and inserts
# it into the appropriate database.

# System
from ntpath import join
import os
import json
from datetime import datetime
from time import sleep

# User library imports
from . import mydb

def fnGetDataDir():
    return os.path.join("/", "data")

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

def fnProcessTweets(record, userData):
    try:
        # Let's get the required fields
        # ID is given for all tweets and it's always an integer. id_str seems redundant
        id = int(record["id"])
        createdAt = datetime.strftime(datetime.strptime(record["created_at"],
                                        '%a %b %d %H:%M:%S +0000 %Y'), '%Y-%m-%d %H:%M:%S')
        text = record["text"]

        #print("Processing tweet id: ", id)
        #print("Created: ", createdAt)
        #print("Text: ", text)
        #print("\n")

        tweetCollection = userData["tweetCollection"]
        tweetCollection.insert_one({
            "id": id,
            "createAt": createdAt,
            "text": text
        })

        # Is rate defined?
        if("rate" in userData):
            rate = userData["rate"]
            sleep(1.0 / rate) # Actual sleep depends on precision of timer

        # Increment progress
        userData["processed"] = userData["processed"] + 1

    except Exception as e:
        print("Error while reading JSON records from memory", e)


def fnReadThreaded(readerData):

    try:
        dbConnection = mydb.fnConnectToMongo()
        if dbConnection != None:
            # Check the MongoDB connection by fetching server info
            serverInfo = dbConnection.server_info()
            #print (serverInfo)

            # Create the database and collection
            tweetCollection = mydb.fnCreateTweetDB(dbConnection)

            # Poor man's objected-oriented (i.e. should use class here)
            readerData["mongoConn"] = dbConnection, 
            readerData["tweetCollection"] = tweetCollection

            inFilepath = readerData["inFilepath"] # A must
            
            # Loop over records in JSON file
            fnGetRecords(inFilepath, fnProcessTweets, None, None, False, readerData)

            mydb.fnDisconnectFromMongo(dbConnection)
    except Exception as error:
        # Need a thread safe way to output errors
        print("Error while reading/processing tweets: ",error)

def fnGetReaderData():
    sampleDataFilepath = os.path.join(fnGetDataDir(), "corona-out-2")
    print("Using file: ", sampleDataFilepath)

    # Poor man's objected-oriented (i.e. should use class here)
    userData = {
        "inFilepath": sampleDataFilepath,
        "rate": 10, # Careful. There is a limit to how precise this is.
        "continue": True, # Adding a control variable here so we can cancel
        "processed": 0, # Records processed
        "progress": 0.0, # estimated progression. 1.0 == complete
    }

    return (userData)
