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