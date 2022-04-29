from warnings import catch_warnings
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from bson import json_util
import json

import threading
from datetime import datetime

# User library
from utils import meta
from utils import pgdb
from utils import redis
from utils import mongodb # TODO: hide this from top level code
from utils import tweet
from utils import ingest_data
from utils import user
from utils import utils

async_mode = None  # "threading", "eventlet" or "gevent"

# TODO: if there's time let's package these in the "create_app" function
# Some globals. Should be stored in a structure
app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)

# Insertion is "single" threaded, i.e. only one user can initiate the injection
insertLock = threading.Lock()
sockLock = threading.Lock()
readerThread = None
updaterThread = None
readerData = None

# Everytime we start clear up the data and init the schema
# fresh start.
ingest_data.fnInitSchemaData()

# Long-lived (runs as soon as the 1st client connects)
def fnThreadUpdates():
    while True:
        global readerData
        progress = 0.0
        processed = 0
        doSend = False

        with insertLock:
            if readerData != None:
                progress = readerData["progress"]
                processed = readerData["processed"]
                doSend = progress > 0 or processed > 0
        
        # If there's a reason to broadcast
        if doSend:
            pctProgress = "{progress: .2f}%".format(progress=progress*100.0)
            socketio.emit('update', {'progress': pctProgress, 'processed': processed})
        
        socketio.sleep(3) # Don't spam the clients too frequently

# Define the "routes" (endpoints) for the Flask web server which will service
# requests
@app.route("/")
def fnRoot():
    return render_template("index.html")

def fnGetTextSearchArgs(args, pgConn):
    # Text(tweet) search
    searchText=request.args.get("searchText")
    sSearchMode=request.args.get("searchMode")
    # Hashtag
    hashtagSearchText=request.args.get("hashtagText")
    sHashtagSearchMode=request.args.get("hashtagSearchMode")
    # People
    peopleSearchText=request.args.get("peopleText")
    sPeopleSearchMode=request.args.get("peopleSearchMode")
    # Place
    placeSearchType=request.args.get("placeSearchType")
    placeSearchName=request.args.get("placeSearchName")
    placeSearchCountry=request.args.get("placeSearchCountry")
    # Date & Misc
    searchStartDate=request.args.get("startDate")
    searchEndDate=request.args.get("endDate")
    searchLanguage=request.args.get("searchLang")
    # Other
    maxResults=int(request.args.get("maxResults"))
    sDisplayOrder=request.args.get("displayOrder")

    # No search parameters defined
    searchArgs = {}

    # Results
    searchArgs["maxResults"] = maxResults
    if sDisplayOrder is not None:
        displayOrder = utils.fnGetDisplayOrder(sDisplayOrder)
        searchArgs["displayOrder"] = displayOrder

    # User may not have specified search text
    if searchText is not None and sSearchMode is not None:
        searchMode = utils.fnGetSearchMode(sSearchMode)
        searchTextModified = utils.fnGetSearchString(searchText, searchMode)

        print("Info: Searching for text {0} using mode {1}".format(searchTextModified, searchMode))
        searchArgs["searchText"] = searchTextModified
        searchArgs["searchMode"] = searchMode

    # Copy paste logic for hashtag search arguments
    if hashtagSearchText is not None and sHashtagSearchMode is not None:
        hashtagSearchMode = utils.fnGetSearchMode(sHashtagSearchMode)
        hashtagSearchTextModified = utils.fnGetSearchTags(hashtagSearchText)

        print("Info: Searching for hashtags {0} using mode {1}".format(hashtagSearchTextModified, hashtagSearchMode))
        searchArgs["searchHashtag"] = hashtagSearchTextModified
        searchArgs["searchHashtagMode"] = hashtagSearchMode

    # People search
    if peopleSearchText is not None and sPeopleSearchMode is not None:
        peopleSearchMode = utils.fnGetPeopleSearchMode(sPeopleSearchMode)
        peopleSearchTextModified = utils.fnGetSearchTags(peopleSearchText)

        # Convert to IDs
        if peopleSearchMode == utils.PeopleSearchMode.FROM or peopleSearchMode == utils.PeopleSearchMode.REPLY:
            peopleSearchTextModified = user.fnGetIDsFromScreenNames(peopleSearchTextModified, pgConn)

        print("Info: Searching for people {0} using mode {1}".format(peopleSearchTextModified, peopleSearchMode))
        searchArgs["searchPeople"] = peopleSearchTextModified
        searchArgs["searchPeopleMode"] = peopleSearchMode

    # Place Search field shouldn't be NULL
    if placeSearchType is not None or placeSearchName is not None or placeSearchCountry is not None:
        print("Searching {0} {1} {2}".format(placeSearchType, placeSearchName, placeSearchCountry))
        lsPlaceIDs = meta.fnGetMatchingPlaceIDs(placeSearchType, placeSearchName, placeSearchCountry, pgConn)
        searchArgs["searchPlace"] = lsPlaceIDs

    # Filter on this date(time) range if one is provided
    if searchStartDate is not None and searchEndDate is not None:
        print("Searching between {0} and {1}".format(searchStartDate, searchEndDate))
        # Store as Python datetime and not strings
        searchArgs["startDate"] = datetime.strptime(searchStartDate, '%Y-%m-%dT%H:%M')
        searchArgs["endDate"] = datetime.strptime(searchEndDate, '%Y-%m-%dT%H:%M')

    # Filter on language if one has been provided
    if searchLanguage is not None:
        print("Info: searching with lang code:", searchLanguage)
        searchArgs["searchLang"] = searchLanguage

    return searchArgs

def fnConvertTweetIDs(tweet):
    try:
        tweet["creator_id"] = str(tweet["creator_id"])
        tweet["reply_to_tweet_id"] = str(tweet["reply_to_tweet_id"])
        tweet["reply_to_user_id"] = str(tweet["reply_to_user_id"])
        tweet["retweet_id"] = str(tweet["retweet_id"])
        tweet["tweet_id"] = str(tweet["tweet_id"])
    except Exception as e:
        print("Error while converting IDs to strings", e)
    
def fnIsSimpleLeaderboardSearch(searchArgs):
    return (len(searchArgs.keys()) == 2 and "maxResults" in searchArgs 
                and "displayOrder" in searchArgs)

def fnCleanupData(lsTweets):
    try:
        for aTweet in lsTweets:
            fnConvertTweetIDs(aTweet)
            # Only convert if it wasn't converted already
            if not isinstance(aTweet["created_at"], str):
                aTweet["created_at"] = aTweet["created_at"].strftime("%m/%d/%Y, %H:%M:%S")
            
    except Exception as e:
        print("Error while cleaning up data", e)

def fnFetchScreeName(pgConnection, lsTweets):
    try:
        for aTweet in lsTweets:
            screen_name = user.fnGetScreenNameFromID(pgConnection, aTweet["creator_id"])
            aTweet["creator_screen_name"] = screen_name
    except Exception as e:
        print("Error while fetching name", e)

@app.route("/search")
def fnSearch():
    
    ret = None
    try:
        mongoConnection = mongodb.fnConnect()
        pgConnection = pgdb.fnConnect()

        maxResults=request.args.get("maxResults")
        displayOrder=request.args.get("displayOrder")
        maxSearchesCached=int(request.args.get("maxSearchesCached"))
        searchCacheExpiry=int(request.args.get("searchCacheExpiry"))
        searchCacheEnabled=bool(request.args.get("searchCacheEnabled"))

        searchArgs = fnGetTextSearchArgs(request.args, pgConnection)

        redisData = redis.fnGetRedisData(searchCacheEnabled, maxResults, searchCacheExpiry, 
                        displayOrder, maxResults, fnIsSimpleLeaderboardSearch(searchArgs))

        print("Searching tweets ...")
        searchArgsAsKey = json.dumps(searchArgs, default=str)
        # Cached results might be a little stale. Tradeoff between seeing
        # tweet results immediately and thrashing db. Check cache control also.
        cachedRes = None
        if searchCacheEnabled:
            print("Cache enabled")
            print(searchArgsAsKey)

            # Try the rank search
            lsTweets = redis.fnFetchRankResults(redisData)
            if lsTweets is not None:
                print("Fetch from rank results")
                fnCleanupData(lsTweets)

                jsonTweets = json_util.dumps(lsTweets)
                ret = {"data": json.loads(jsonTweets) }
            else:
                cachedRes = redis.fnFetchSearchResults(redisData, searchArgsAsKey)
        
        if cachedRes is None:
            print("Fetch from db")
            lsTweets = tweet.fnGetFiltered(mongoConnection, searchArgs)

            fnCleanupData(lsTweets)
            fnFetchScreeName(pgConnection, lsTweets)

            jsonTweets = json_util.dumps(lsTweets)
            ret = {"data": json.loads(jsonTweets) }
            
            # Only cache if there were some results and cache is enabled
            if searchCacheEnabled and len(lsTweets) > 0:
                redis.fnCacheSearchResults(redisData, searchArgsAsKey, jsonTweets)
        else:
            print("Fetch from cache")
            ret = {"data": json.loads(cachedRes) }
        
        if(mongoConnection is not None):
            mongodb.fnDisconnect(mongoConnection)

        if(pgConnection is not None):
            pgdb.fnDisconnect(pgConnection)

    except Exception as error:
        print("Error: could not search tweets:", error)

    return ret #render_template("index.html", tweets=lsTweets)

@app.route("/insert")
def fnInsert():
    global readerThread
    global readerData
    # Make sure one user can get in and trigger start/stop
    with insertLock:
        # Is thread in progress
        if (readerThread is None):
            try:
                doStream = False
                insertDelay = 0

                streamArg=request.args.get("stream")
                if streamArg is not None and streamArg == "1":
                    print("Info: Streaming mode enabled")
                    doStream = True
                else:
                    print("Warning: stream argument is not valid: ", streamArg)

                # Only relavent for streaming
                if doStream:
                    insertDelayArg=int(request.args.get("insertDelay"))
                    print("Info: stream delay is: ", insertDelayArg)

                sampleArg=request.args.get("sample")
                if sampleArg is not None:
                    print("Arguments for insertion are: stream: {0}, delay: {1}, sample: {2}", streamArg, 
                            insertDelayArg, sampleArg)

                    readerData = ingest_data.fnGetReaderData(sampleArg, insertDelayArg)
                    readerData["isIngesting"] = True
                    readerThread = threading.Thread(target=ingest_data.fnReadThreaded, args=(readerData,))
                    readerThread.start()
                else:
                    # TODO: return meaningful error. Need 403 and possibly base.html template
                    print("Error: please specify a sample file to ingest")

            except Exception as error:
                print("Error while trigger job: ", error)
        
    return render_template("index.html")

@app.route("/clear")
def fnClearDB():
    global readerData
    # Prevent clearing of DB while data is being inserted
    with insertLock:
        okToClear = readerData is None or not readerData["isIngesting"]
        if(okToClear):
            ingest_data.fnClearData()
        elif readerData is not None:
            # TODO: return meaningful error. Need 403 and possibly base.html template
            print("Error: currently ingesting data. Please wait ...")

        socketio.emit('update', {'progress': 0, 'processed': 0})

    return render_template("index.html")

@app.route("/stop")
def fnStop():
    global readerThread
    global readerData

    with insertLock:
        # Is thread in progress
        if (not readerThread is None):
            try:
                readerData["continue"] = False
                readerThread.join()
                readerData = None
                readerThread = None
            except Exception as error:
                print("Error while stopping job: ", error)
    # Send stop update
    socketio.emit('stopped')

    return render_template("index.html")

@app.route("/tweet")
def fnGetTweetFromID():
    ret = {}

    try:
        tweetID=int(request.args.get("tweet_id"))

        mongoConnection = mongodb.fnConnect()
        pgConnection = pgdb.fnConnect()

        lsTweets = tweet.fnGetTweet(mongoConnection, tweetID)
        for aTweet in lsTweets:
            screen_name = user.fnGetScreenNameFromID(pgConnection, aTweet["creator_id"])
            aTweet["creator_screen_name"] = screen_name
            fnConvertTweetIDs(aTweet)

        if(mongoConnection is not None):
            mongodb.fnDisconnect(mongoConnection)

        if(pgConnection is not None):
            pgdb.fnDisconnect(pgConnection)

        ret = {"data": json.loads(json_util.dumps(lsTweets)) }

    except Exception as e:
        print("Error: could not fetch tweet due to:", e)

    return ret

@app.route("/languages")
def fnGetLanguages():
    lsLangs = meta.fnGetAllLanguages()
    #print("Get languages", lsLangs)
    return {"languages": lsLangs}

@app.route("/place_types")
def fnGetPlaceTypes():
    lsPlaceTypes = meta.fnGetAllPlaceTypes()
    print("Get place types", lsPlaceTypes)
    return {"place_types": lsPlaceTypes}

@app.route("/place_countries")
def fnGetPlaceCountries():
    lsPlaceCountries = meta.fnGetAllPlaceCountries()
    print("Get place types", lsPlaceCountries)
    return {"place_types": lsPlaceCountries}

@socketio.on('get_updates')
def fnGetUpdates():
    print("Received request from client: ")

@socketio.event
def connect():
    print("Client connected")
    global updaterThread
    with sockLock:
        try:
            if updaterThread is None:
                updaterThread = socketio.start_background_task(fnThreadUpdates)
        except Exception as error:
            print("Error while trying to start updater thread: ", error)