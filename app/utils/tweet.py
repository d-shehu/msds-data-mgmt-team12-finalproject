# Data stores
from datetime import datetime

from time import sleep

from . import mongodb
from . import meta
from . import user

# Since we're not given a retweet ID let's process the status and grab it there.
def fnProcessRetweet(record, userData):
    try:
        # TODO: for now let's assume the original tweet is in the feed as well. If this
        # assumption is bad we can process the status for retweets
        return record["id"]
    except Exception as e:
        print("Error while parsing retweet status from memory", e)

def fnProcessTweets(record, userData):
    try:
        # Let's get the required fields
        # ID is given for all tweets and it's always an integer. id_str seems redundant
        createdAt = datetime.strftime(datetime.strptime(record["created_at"],
                                        '%a %b %d %H:%M:%S +0000 %Y'), '%Y-%m-%d %H:%M:%S')

        #print("Processing tweet id: ", id)
        #print("Created: ", createdAt)
        #print("Text: ", text)
        #print("\n")

        # Extract tags from entities (if any)
        lsTags, lsMentions = fnProcessEntities(record, userData)

        retweetID = None
        if "retweet_status" in record:
            retweetID = fnProcessRetweet(record["retweeted_status"])

        quotedStatusID = None
        if "quote_status_id" in record:
            quotedStatusID = record["quote_status_id"]

        inReplyToStatusID = None
        if "in_reply_to_status_id" in record:
            inReplyToStatusID = record["in_reply_to_status_id"]

        placeID = None
        if "place" in record and record["place"] is not None:
            placeID = meta.fnProcessPlace(record["place"], userData)

        # Grab the creator
        creatorID = user.fnProcessUser(record["user"], userData)

        # Language code is 1:1 (not sparse) it seems
        langCode = record["lang"]
        meta.fnInsertLanguage(langCode, userData)

        tweetCollection = userData["tweetCollection"]
        tweetCollection.insert_one({
            "tweet_id":             record["id"],
            "created_at":           createdAt,
            "text":                 record["text"],
            "source":               record["source"],
            "creator_id":           creatorID,
            # Reply/retweet references. These IDs are given and 
            # TODO: we assume for now the tweets are in the feed. If not
            # this may cause an issue.
            "reply_to_tweet_id":    inReplyToStatusID,
            "quote_tweet_id":       quotedStatusID,
            "retweet_id":           retweetID,
            # Tweet stats
            "quote_count":          record["quote_count"],
            "reply_count":          record["reply_count"],
            "retweet_count":        record["retweet_count"],
            "favorite_count":       record["favorite_count"],
            # Tags
            "hashtags":             lsTags,
            "user_mentions":        lsMentions,
            # Other
            "place_id":             placeID,
            "lang_code":            langCode   
        })

        # Is rate defined?
        if("delay" in userData):
            delay = userData["delay"]
            sleep(delay/1000.0) # Actual sleep depends on precision of timer

        # Increment progress
        userData["processed"] = userData["processed"] + 1

    except Exception as e:
        print("Error while parsing tweet JSON records from memory", e)
    
def fnProcessEntities(record, userData):

    lsTags = []
    lsMentions = []

    try:
        entities = record["entities"]
        if entities is not None:
            # Keeping only hashtags and mentions since those seem the
            # most useful in terms of tags/categories for the data 
            hashTags = entities["hashtags"]
            if hashTags is not None:
                for tag in hashTags:
                    # Only care about the text and not it's position
                    if "text" in tag:
                        # Twitter parses every instance of hashtag
                        # but we only search on the unique instance
                        # so let's just keep those
                        if not tag["text"] in lsTags:
                            lsTags.append(tag["text"])
                    else:
                        print("Warning: hashtag missing text")
            
            userMentions = entities["user_mentions"]
            if userMentions is not None:
                for user in userMentions:
                    # Only care about the screen name
                    if "screen_name" in user:
                        lsMentions.append(user["screen_name"])
                    else:
                        print("Warning: user mention missing screen_name")
        else:
            print("Warning: there should be at least 1 entity for this tweet:", record["id"])
        
    except Exception as e:
        print("Error while parsing entities record", e)

    return lsTags, lsMentions

# Let's include the full tweet text. There is no limitation
# on Mongo so we can just replace the truncated text with full text
def fnProcessExtendedEntities(record, userData):
    try:
        # Start with the hashtags and expand. This will be a list
        # of "tags" (SearchApp) and hashtag is a type of tag supported
        print("Not implemented yet")
    except Exception as e:
        print("Error while parsing entities JSON records from memory", e)
  

def fnGetFiltered(dbConnection, searchArgs):
    lsTweets = []

    try:
        maxResults = searchArgs["maxResults"]

        print("Get tweets collection")
        tweetCollection,tagCollection = mongodb.fnGetCollections(dbConnection)

        searchCriteria = {}
        
        # TODO: this code should move to the mongodb python file
        # Search criteria includes text
        if "searchText" in searchArgs:
            print("Info: Mongo Search Filter is ", searchArgs["searchText"])
            mongodb.fnSearchText(searchCriteria, "text", searchArgs["searchText"])
        # This is a bit more complex. Search hashtag in collection to get the ids
        # then do a search
        if "searchHashtag" in searchArgs:
            print("Info: Mongo Tag Filter is ", searchArgs["searchHashtag"]) 
            mongodb.fnSearchTags(searchCriteria, "hashtags", searchArgs["searchHashtag"], 
                                    searchArgs["searchHashtagMode"])
        # Modify search criteria to include dates?
        if "startDate" in searchArgs and "endDate" in searchArgs:
            print("Info: Mongo Start Date Filter is ", searchArgs["startDate"])
            print("Info: Mongo End Date Filter is ", searchArgs["endDate"])
            mongodb.fnSearchRange(searchCriteria, "created_at", searchArgs["startDate"], searchArgs["endDate"])
        # Search criteria includes language
        if "searchLang" in searchArgs:
            print("Info: Searching for Language", searchArgs["searchLang"])
            mongodb.fnSearchExactValue(searchCriteria, "lang_code", searchArgs["searchLang"])
            searchCriteria["lang_code"] = {'$eq': searchArgs["searchLang"]}

        print("Info: Mongo search criteria: ", searchCriteria)
        lsTweets = list(tweetCollection.find(searchCriteria).limit(maxResults))

    except Exception as error:
        print("Unable to fetch tweets from Mongo: ", error)

    return lsTweets