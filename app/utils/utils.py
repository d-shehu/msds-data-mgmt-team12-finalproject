import enum
from tkinter import UNDERLINE
from unittest import load_tests
 
class SearchMode(enum.Enum):
    EXACT   = 1
    ALL     = 2
    ANY     = 3
    UND     = 4

class PeopleSearchMode(enum.Enum):
    FROM        = 1
    REPLY       = 2
    MENTION     = 3
    UND         = 4

class DisplayOrder(enum.Enum):
    LATEST          = 1
    POPULAR         = 2
    AUTHORITATIVE   = 3
    INFLUENCE       = 4
    UND             = 5

# Get enum from text
def fnGetSearchMode(sSearchMode):

    ret = SearchMode.UND
    if(sSearchMode == "exact" ):
        ret = SearchMode.EXACT
    elif(sSearchMode == "all" ):
        ret = SearchMode.ALL
    elif(sSearchMode == "any"):
        ret = SearchMode.ANY
    else:
        print("Error: unexpected search mode", sSearchMode)
    
    return ret

def fnGetPeopleSearchMode(sSearchMode):

    ret = PeopleSearchMode.UND
    if(sSearchMode == "from"):
        ret = PeopleSearchMode.FROM
    elif(sSearchMode == "reply"):
        ret = PeopleSearchMode.REPLY
    elif(sSearchMode == "mention"):
        ret = PeopleSearchMode.MENTION
    else:
        print("Error: unexpected people search mode", sSearchMode)
    
    return ret

def fnGetDisplayOrder(sDisplayOrder):

    ret = DisplayOrder.UND
    if (sDisplayOrder == "latest"):
        ret = DisplayOrder.LATEST
    elif (sDisplayOrder == "popular"):
        ret = DisplayOrder.POPULAR
    elif (sDisplayOrder == "authoritative"):
        ret = DisplayOrder.AUTHORITATIVE
    elif (sDisplayOrder == "influence"):
        ret = DisplayOrder.INFLUENCE
    else:
        print("Error: unexpected display order", sDisplayOrder)
    
    return ret

def fnGetSearchString(searchText, searchMode):

    # For ANY just pass in as
    sModified = searchText
    # Match phrase exactly
    if (searchMode == SearchMode.EXACT):
        # Strip quotes from the string since string is used to specify exact
        # Unfortunately this is a limitation
        sModified = searchText.replace("\"", "")
        sModified = "\"{0}\"".format(sModified)
    elif (searchMode == SearchMode.ALL):
        # See comment above
        sModified = searchText.replace("\"", "")
        # tokenize
        lsTokenList = sModified.split()

        sModified = ""
        for sToken in lsTokenList:
            sModified = sModified + "\"{0}\" ".format(sToken)
    
    print("Info: modified search term: ", sModified)

    return sModified

def fnGetSearchTags(sSearchText):
    # Always tokenize the search string 
    lsTokenList = sSearchText.split()

    return lsTokenList

def fnGetSQLSafeStr(sIn):
    # Handle quotes in the name so query doesn't break
    return sIn.replace("'", "''")