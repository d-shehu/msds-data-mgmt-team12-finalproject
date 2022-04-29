import os
import psycopg

def fnConnect():
    dbConnection = None
    try:
        sConnectionString = "host='{0}' dbname='{1}' user='{2}' password='{3}'".format(
            os.getenv('PG_DB_HOSTNAME'),
            "postgres", # TODO: currently using postgres database but we should use a different one
            os.getenv('PG_DB_USERNAME'),
            os.getenv('PG_DB_PASSWORD')
        )
        dbConnection = psycopg.connect(sConnectionString)
        # Turn off transactions. They get in the way during development
        dbConnection.autocommit = True

    except Exception as e:
        print("Error: exception while establishing a connection to Postgres: ", e)
    
    return dbConnection

def fnDisconnect(dbConnection):
    try:
        dbConnection.close()
    except Exception as e:
        print("Error: while trying to disconnect from Postgres")

# Initialize the DB with the latest schema
def fnInitSchema(dbConnection):
    if dbConnection != None:
        try:
            # Need to create the cursor for executing any statement
            # TODO: Location will be refactored to make it a fk to place
            with dbConnection.cursor() as curs:

                # Trigram Postgres extension allow for fuzzy search on fields
                # Needs to be installed as it may not come with Postgres default install
                curs.execute("""CREATE EXTENSION IF NOT EXISTS pg_trgm;
                                CREATE EXTENSION IF NOT EXISTS btree_gin;
                             """)

                # Create the user and other pg tables
                # TODO: Postgres should automatically create a clustered index
                # on the primary key (id) and a non clustered index on the UNIQUE field
                # Double check this!
                # Create the Language table

                # Meta data - should be initialized ahead of time
                # Create the Language table
                curs.execute("""DROP TABLE IF EXISTS language CASCADE;
                                CREATE TABLE language(
                                    code CHAR(2) PRIMARY KEY,
                                    language VARCHAR(64) NOT NULL UNIQUE
                                );
                            """)

                # Create the Place table
                # TODO: consider replacing type with an enum depending on how
                # many options exist in Twitter data.
                curs.execute("""DROP TABLE IF EXISTS place CASCADE;
                                CREATE TABLE place(
                                    id serial PRIMARY KEY,
                                    original_id text UNIQUE,
                                    type VARCHAR(64),
                                    name VARCHAR(64),
                                    country VARCHAR(64),
                                    country_code CHAR(2)
                                );
                                CREATE INDEX tbl_place_type_idx ON place USING gin (type);
                                CREATE INDEX tbl_place_city_idx ON place USING gin (name);
                                CREATE INDEX tbl_place_country_idx ON place USING gin (country);
                            """)

                # User is a reserved word in psql. So call it user_
                # Need to establish a foreign key relationship with lang table
                curs.execute("""DROP TABLE IF EXISTS user_ CASCADE;
                                CREATE TABLE user_(
                                    id BIGINT PRIMARY KEY,
                                    screen_name VARCHAR(64) NOT NULL UNIQUE,
                                    location VARCHAR(64),
                                    follower_count INTEGER,
                                    friends_count INTEGER,
                                    listed_count INTEGER,
                                    created_at TIMESTAMP,
                                    lang_code INTEGER,
                                    last_updated_ts BIGINT
                                );
                            """)
                
                
                # Create the stats table for tracking counts and other metrics
                curs.execute("""DROP TABLE IF EXISTS stats CASCADE;
                                CREATE TABLE Stats(
                                    numTweets BIGINT,
                                    numRetweets BIGINT
                                );
                            """)
        except Exception as e:
            print("Error: unable to initialize the schema", e)
    else:
        print("DB connection is not valid")

def fnClearData(dbConnection):
    if dbConnection != None:
        try:
            # Need to create the cursor for executing any statement
            # TODO: Location will be refactored to make it a fk to place
            with dbConnection.cursor() as curs:
                # Delete the non-meta data
                curs.execute("DELETE * from user_;")

        except Exception as e:
            print("Error: unable to initialize the schema", e)
    else:
        print("DB connection is not valid")

def fnGetIDFromScreenName(dbConnection, screenName):
    outID=None

    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT id FROM user_ WHERE screen_name='{0}'".format(screenName))

            # Assuming screenname is unique as defined in the schema
            idRec = curs.fetchone()
            outID = idRec[0]
            
    except Exception as e:
        print("Info: user with screen name not found or field was missing: ", screenName)

    return outID

def fnGetUserFromID(dbConnection, id):
    outUser=None
        
    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT * FROM user_ WHERE id={0}".format(id))

            # Construct dict obj for user. There can only be 1 as it's the PK
            userRec = curs.fetchone()
            if(userRec is not None):
                outUser = {
                    "id":               id,
                    # Psycopg does not support fetching by column name
                    # So take care if changing columns/order in schema
                    "screen_name":      userRec[1],
                    "location":         userRec[2],
                    "follower_count":   userRec[3],
                    "friends_count":    userRec[4],
                    "listed_count":     userRec[5],
                    "created_at":       userRec[6],
                    "lang_code":        userRec[7],
                    "last_updated_ts":  userRec[8]
                }

    except Exception as e:
        print("Info: user with id not found or field was missing: ", id)
    
    return outUser

def fnInsertUser(dbConnection, id, screenName, location, followerCount, friendsCount, 
                    listedCount, createdAt, langCode, lastUpdatedTS):
    try:
        sQuery = ""
        # If the user exists, let's see if this info is more up to date (counts, screenname)
        dbUser = fnGetUserFromID(dbConnection, id)
        if dbUser is None:
            # TODO: fix language code
            sQuery = """INSERT INTO user_ (id, screen_name, location, follower_count,
                        friends_count, listed_count, created_at, lang_code, last_updated_ts)
                        VALUES ({0}, '{1}', '{2}', {3}, {4}, {5}, '{6}', {7}, {8})
                    """.format(id, screenName, location, followerCount, friendsCount,
                    listedCount, createdAt, 0, lastUpdatedTS)
                
        # Incoming user is coming from a more recent tweet. If any info has changed
        # update the record
        # TODO: check assumption if lang code or created_at can change
        elif (dbUser["last_updated_ts"] < lastUpdatedTS and 
                (dbUser["screen_name"] != screenName or dbUser["location"] != location
                or dbUser["follower_count"] != followerCount or dbUser["friends_count"] != friendsCount
                or dbUser["listed_count"] != listedCount)):
            #print("Updating user ", dbUser["screen_name"], "who is now ", screenName)
            # TODO: fix language code
            sQuery = """UPDATE user_ SET screen_name='{0}', location='{1}', follower_count={2},
                                friends_count={3}, listed_count={4}, last_updated_ts={5}
                        WHERE id={6}        
                    """.format(screenName, location, followerCount, friendsCount,
                                listedCount, lastUpdatedTS, id)
        
        if sQuery != "":
            with dbConnection.cursor() as curs:        
                curs.execute(sQuery)
            

    except Exception as e:
        print("Error while trying to insert/update a user: ", e, sQuery)

def fnFindLanguage(dbConnection, langCode):

    outLanguage=None

    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT * FROM language WHERE code='{0}'".format(langCode))

            # Construct dict obj for lang. There can only be 1 as it's the PK
            langRec = curs.fetchone()
            if(langRec is not None):
                outLanguage = {
                    "code":     langCode,  
                    "language": langRec[1]
                }

    except Exception as e:
        print("Info: language with code not found or other issue: ", langCode)

    return outLanguage

def fnInsertLanguage(dbConnection, langCode, language):

    try:
        dbLanguage = fnFindLanguage(dbConnection, langCode)
        if dbLanguage is None:
            with dbConnection.cursor() as curs:
                sQuery = """INSERT INTO language (code, language)
                            VALUES ('{0}', '{1}')
                        """.format(langCode, language)
                
                curs.execute(sQuery)

    except Exception as e:
        print("Error while trying to insert language '", langCode, "': ", e)

def fnGetAllLanguages(dbConnection):
    lsLanguages=[]

    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT * FROM language ORDER BY language")

            # Grab them all
            langRecs = curs.fetchall()
            for langRec in langRecs:
                lsLanguages.append({
                    "code":     langRec[0],  
                    "language": langRec[1]
                })

    except Exception as e:
        print("Info: error while fetching languages from the database")

    return lsLanguages

def fnGetPlaceFromResult(dbRecord):
    outPlace=None

    if(dbRecord is not None):
        outPlace = {
            "id":           dbRecord[0],
            "original_id":  dbRecord[1],
            "type":         dbRecord[2],
            "name":         dbRecord[3],
            "country":      dbRecord[4],
            "countryCode":  dbRecord[5]
        }
        
    return outPlace

def fnGetPlaceFromID(dbConnection, id):
    outPlace=None
        
    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT * FROM place WHERE id='{0}'".format(id))

            outPlace = fnGetPlaceFromResult(curs.fetchone())
    except Exception as e:
        print("Info: place with id not found or field was missing: ", id)
    
    return outPlace

def fnGetPlaceFromOriginalID(dbConnection, originalID):
    outPlace=None
        
    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT * FROM place WHERE original_id='{0}'".format(originalID))

            outPlace = fnGetPlaceFromResult(curs.fetchone())
    except Exception as e:
        print("Info: place with original(twitter) id not found or field was missing: ", originalID)
    
    return outPlace

def fnInsertPlace(dbConnection, originalID, placeType, placeName, country, countryCode):

    newID = None

    try:
        # Only insert if the user hasn't been added before
        dbPlace = fnGetPlaceFromOriginalID(dbConnection, originalID)
        if dbPlace is None:
            # TODO: fix language code
            with dbConnection.cursor() as curs:
                sQuery = """INSERT INTO place (original_id, type, name, country, country_code)
                            VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') RETURNING id;
                        """.format(originalID, placeType, placeName, country, countryCode)
                
                curs.execute(sQuery)

                # Should return the serial (new id)
                newID = (curs.fetchone())[0]
                #print("New place id is:", newID)

    except Exception as e:
        print("Error while trying to insert place: ", e)

    return newID

def fnGetAllPlaceTypes(dbConnection):
    lsPlaceTypes=[]

    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT DISTINCT type FROM place ORDER BY type")

            # Grab them all
            typeRecs = curs.fetchall()
            for typeRec in typeRecs:
                lsPlaceTypes.append(typeRec[0])

    except Exception as e:
        print("Info: error while fetching place types from the database")

    return lsPlaceTypes

def fnGetAllPlaceCountries(dbConnection):
    lsPlaceCountries=[]

    try:
        with dbConnection.cursor() as curs:
            curs.execute("SELECT DISTINCT country FROM place ORDER BY country")

            # Grab them all
            countryRecs = curs.fetchall()
            for countryRec in countryRecs:
                lsPlaceCountries.append(countryRec[0])

    except Exception as e:
        print("Info: error while fetching place countries from the database")

    return lsPlaceCountries


def fnGetMatchingPlaceIDs(dbConnection, sType, sName, sCountry):
    lsPlaceIDs=[]

    try:
        with dbConnection.cursor() as curs:
            sClause = ""
            if sType is not None:
                sClause = sClause + " type='{0}'".format(sType)

            if sName is not None:
                if sClause != "":
                    sClause = sClause + " and"
                sClause = sClause + " name='{0}'".format(sName)

            if sCountry is not None:
                if sClause != "":
                    sClause = sClause + " and"
                sClause = sClause + " country='{0}'".format(sCountry)

            curs.execute("SELECT original_id FROM place where" + sClause)

            # Grab them all
            countryRecs = curs.fetchall()
            for countryRec in countryRecs:
                lsPlaceIDs.append(countryRec[0])

    except Exception as e:
        print("Info: error while fetching places from the database matching {0}, {1}, {2}: ".format(sType, sName,sCountry), e)

    return lsPlaceIDs