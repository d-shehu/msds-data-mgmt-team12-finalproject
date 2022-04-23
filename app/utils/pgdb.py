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
                                    id SERIAL PRIMARY KEY,
                                    name VARCHAR(64),
                                    type VARCHAR(64),
                                    country VARCHAR(64)
                                );
                                CREATE INDEX tbl_place_city_idx ON place USING gin (name);
                                CREATE INDEX tbl_place_type_idx ON place USING gin (type);
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
                                    lang_code INTEGER
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
                    "lang_code":        userRec[7]
                }

    except Exception as e:
        print("Info: user with id not found or field was missing: ", id)
    
    return outUser

def fnInsertUser(dbConnection, id, screenName, location, followerCount, friendsCount, 
                    listedCount, createdAt, langCode):
    try:
        # Only insert if the user hasn't been added before
        dbUser = fnGetUserFromID(dbConnection, id)
        if dbUser is None:
            # TODO: fix language code
            with dbConnection.cursor() as curs:
                sQuery = """INSERT INTO user_ (id, screen_name, location, follower_count,
                            friends_count, listed_count, created_at, lang_code)
                            VALUES ({0}, '{1}', '{2}', {3}, {4}, {5}, '{6}', {7})
                        """.format(id, screenName, location, followerCount, friendsCount,
                        listedCount, createdAt, 0)
                
                curs.execute(sQuery)

    except Exception as e:
        print("Error while trying to insert user: ", e)

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
