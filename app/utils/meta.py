from warnings import catch_warnings
import pycountry

from . import pgdb
from . import utils

def fnInsertCountry(countryCode):
    try:
        country = pycountry.countries.get(alpha_2=countryCode)
        countryName = country["name"]
    except Exception as e:
        print("Error while trying to add country: ", e)

def fnInsertLanguage(langCode, userData):
    try:
        pgConnection = userData["pgConn"]
        langEntry = pycountry.languages.get(alpha_2=langCode)
        if langEntry is not None:
            language = langEntry.name
            pgdb.fnInsertLanguage(pgConnection, langCode, language)
        # Unknown language code
        elif langCode == "und":
            pgdb.fnInsertLanguage(pgConnection, "??", "UNDEFINED")
        # More made up iso2 codes from Twitter
        else:
            # Unexpected ISO2 language code
            pgdb.fnInsertLanguage(pgConnection, langCode, "ERR:" + langCode)

    except Exception as e:
        print("Error while trying to add language: ", e)

# Wrapper functions. May add caching later if performance warrants it
def fnGetAllLanguages(pgConnection=None):
    lsLanguages = []

    try:
        createConn=pgConnection is None
        if createConn:
            pgConnection = pgdb.fnConnect()

        # TODO: add caching here possibly?
        lsLanguages = pgdb.fnGetAllLanguages(pgConnection)

        if createConn:
            pgdb.fnDisconnect(pgConnection)
    except Exception as e:
        print("Error unable to get language from database")

    return lsLanguages

def fnProcessPlace(placeRecord, userData):

    id = None
    try:
        pgConnection = userData["pgConn"]
        id = placeRecord["id"]
        pgdb.fnInsertPlace(pgConnection, id, placeRecord["place_type"], 
                            utils.fnGetSQLSafeStr(placeRecord["name"]), placeRecord["country"], placeRecord["country_code"])
    except Exception as e:
        print("Error while parsing place", e)

    return id

def fnGetAllPlaceTypes(pgConnection=None):
    lsPlaceTypes = []

    try:
        createConn=pgConnection is None
        if createConn:
            pgConnection = pgdb.fnConnect()

        lsLanguages = pgdb.fnGetAllPlaceTypes(pgConnection)

        if createConn:
            pgdb.fnDisconnect(pgConnection)
    except Exception as e:
        print("Error unable to get languages from database")

    return lsLanguages

def fnGetAllPlaceCountries(pgConnection=None):
    lsPlaceCountries = []

    try:
        createConn=pgConnection is None
        if createConn:
            pgConnection = pgdb.fnConnect()

        lsPlaceCountries = pgdb.fnGetAllPlaceCountries(pgConnection)

        if createConn:
            pgdb.fnDisconnect(pgConnection)
    except Exception as e:
        print("Error: unable to get countries from database:", e)

    return lsPlaceCountries

# TODO: wrapper that could be used to cache results in Redis
def fnGetMatchingPlaceIDs(sType, sName, sCountry, pgConnection=None):
    lsPlaceIDs = []

    try:
        createConn=pgConnection is None
        if createConn:
            pgConnection = pgdb.fnConnect()

        lsPlaceIDs = pgdb.fnGetMatchingPlaceIDs(pgConnection, sType, sName, sCountry)

        if createConn:
            pgdb.fnDisconnect(pgConnection)  
    except Exception as e:
        print("Error while trying to fetch places")

    return lsPlaceIDs
