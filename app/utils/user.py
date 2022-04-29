from datetime import datetime

import math

from . import pgdb
from . import utils

# This function inserts records one at a time as with Mongo
# Since it "commits" after each insert it can be a bit slow
# when inserting a larger number of records.
def fnProcessUser(record, userData, timestampInMillis):

    id = None
    influence = 0

    try:
        pgConnection    = userData["pgConn"]

        # Let's assume we can just use the
        id              = int(record["id"])
        screenName      = record["screen_name"]
        createdAt       = datetime.strftime(datetime.strptime(record["created_at"],
                                        '%a %b %d %H:%M:%S +0000 %Y'), '%Y-%m-%d %H:%M:%S')

        # TODO this should be converted to a location ID using associated func
        #location        = record["location"] 
        #fnProcessPlace(record["location"] )

        followersCount  = record["followers_count"]
        friendsCount    = record["friends_count"]
        listedCount     = record["listed_count"]

        # Weight the followers and friends
        influence = int(math.sqrt(followersCount*followersCount + friendsCount*friendsCount))

        # Handle quotes in the name so query doesn't break
        screenNameModified = utils.fnGetSQLSafeStr(screenName)

        # TODO fixed language code
        pgdb.fnInsertUser(pgConnection, id, screenName, "", followersCount, friendsCount,
                            listedCount, createdAt, 0, timestampInMillis) 

    except Exception as e:
        print("Error while parsing place JSON records from memory", e)
    
    #print("{0} with influence {1}".format(screenName, influence))
    # Must return an id
    return id, influence

def fnGetScreenNameFromID(dbConnection, id):

    screenName = ""

    try:
        user = pgdb.fnGetUserFromID(dbConnection, id)
        screenName = user["screen_name"]
    except Exception as e:
        print("Error while fetching screenname from id", id)

    return screenName

def fnGetIDsFromScreenNames(lsScreenNames, dbConnection):

    lsIDs = []

    for screenName in lsScreenNames:
        id = pgdb.fnGetIDFromScreenName(dbConnection, screenName)
        if(id is not None):
            lsIDs.append(id)

    return lsIDs

