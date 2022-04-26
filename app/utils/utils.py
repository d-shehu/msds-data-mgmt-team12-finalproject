import enum
 
class SearchMode(enum.Enum):
    EXACT   = 1
    ALL     = 2
    ANY     = 3
    UND     = 4

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
        print("Error: unexpected search mode")
    
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

def fnGetSearchTags(sSearchText, searchMode):
    # Always tokenize the search string 
    lsTokenList = sSearchText.split()

    return lsTokenList

def fnGetSQLSafeStr(sIn):
    # Handle quotes in the name so query doesn't break
    return sIn.replace("'", "''")