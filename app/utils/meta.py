from warnings import catch_warnings
import pycountry

from . import pgdb

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

# Wrapper function, may add some caching later if performance warrants it
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