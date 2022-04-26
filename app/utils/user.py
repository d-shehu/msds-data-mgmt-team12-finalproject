from datetime import datetime

from . import pgdb
from . import utils

# This function inserts records one at a time as with Mongo
# Since it "commits" after each insert it can be a bit slow
# when inserting a larger number of records.
def fnProcessUser(record, userData):

    id = None

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

        # Handle quotes in the name so query doesn't break
        screenNameModified = utils.fnGetSQLSafeStr(screenName)

        # TODO fixed language code
        pgdb.fnInsertUser(pgConnection, id, screenName, "", followersCount, friendsCount,
                            listedCount, createdAt, 0) 

    except Exception as e:
        print("Error while parsing place JSON records from memory", e)
    
    # Must return an id
    return id

def fnGetScreenNameFromID(dbConnection, id):

    screenName = ""

    try:
        user = pgdb.fnGetUserFromID(dbConnection, id)
        screenName = user["screen_name"]
    except Exception as e:
        print("Error while fetching screenname from id", id)

    return screenName
