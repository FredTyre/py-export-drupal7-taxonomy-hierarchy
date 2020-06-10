import MySQLdb
import re

ENDL = '\n'

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'

currentWebsite = "example"
dbHost = 'hostname.example.com'
dbPort = 3306
dbUser = 'user'
dbPassword = 'password'
dbDatabase = 'database'

ignoreCaseReplaceEndlines1 = re.compile("<br/>", re.IGNORECASE)
ignoreCaseReplaceEndlines2 = re.compile("<br />", re.IGNORECASE)
ignoreCaseReplaceEndlines3 = re.compile("<br>", re.IGNORECASE)
ignoreCaseReplaceParagraphTagBegin = re.compile("<p>", re.IGNORECASE)
ignoreCaseReplaceParagraphTagEnd = re.compile("</p>", re.IGNORECASE)
ignoreCaseReplaceSpace = re.compile("&nbsp;", re.IGNORECASE)
ignoreCaseReplaceDollarSign = re.compile("\$", re.IGNORECASE)
ignoreCaseReplaceComma = re.compile(",", re.IGNORECASE)
ignoreCaseReplaceLeftParenthesis = re.compile("\(", re.IGNORECASE)
ignoreCaseReplaceRightParenthesis = re.compile("\)", re.IGNORECASE)
ignoreCaseReplaceNegative = re.compile("-", re.IGNORECASE)
ignoreCaseReplaceForwardSlash = re.compile("[/]+", re.IGNORECASE)
ignoreCaseReplaceLetters = re.compile("[a-z]+", re.IGNORECASE)
ignoreCaseReplacePeriod = re.compile("[\.]+", re.IGNORECASE)

def removeEmptyLines(string2Fix, endLine):
    returnString = ""

    lines = string2Fix.split(endLine)
    for line in lines:
        if(line is None):
            continue
        
        if(len(line.strip()) > 0):
            returnString += line + endLine

    return returnString

def shrinkWidth(string2shrink, newWidth):    
    returnString = ""
    
    currentLineLength = 0
    firstWord = True
    for currentWord in string2shrink.split(" "):
        if(not firstWord and currentLineLength > newWidth):
            returnString += ENDL
            currentLineLength = 0
            firstWord = True
            
        returnString += currentWord + " "
        currentLineLength += len(currentWord) + 1
        firstWord = False

    returnString = removeEmptyLines(returnString, ENDL)
    
    return returnString.strip()

def convertHTML(string2Convert, endLine):
    if(string2Convert is None):
        return ""
    
    returnString = string2Convert
    returnString = ignoreCaseReplaceEndlines1.sub(endLine, returnString)
    returnString = ignoreCaseReplaceEndlines2.sub(endLine, returnString)
    returnString = ignoreCaseReplaceEndlines3.sub(endLine, returnString)
    returnString = ignoreCaseReplaceParagraphTagBegin.sub("", returnString)
    returnString = ignoreCaseReplaceParagraphTagEnd.sub("", returnString)
    returnString = ignoreCaseReplaceSpace.sub(" ", returnString)

    returnString = removeEmptyLines(returnString, endLine)
    # print('================================================\n' + string2Convert + '--------------------------------------\n' + returnString + '================================================\n')
    
    return returnString.strip()

def printEmptyLine(proofOutputFileHandle, outputFileHandle):
    outputFileHandle.write(ENDL)
    
def flushPrintFiles(debugOutputFileHandle, outputFileHandle):
    debugOutputFileHandle.flush()
    outputFileHandle.flush()
    
def getVocabularies(debugOutputFileHandle):
    conn = MySQLdb.connect(host=dbHost, user=dbUser, passwd=dbPassword, database=dbDatabase, port=dbPort)
    cursor = conn.cursor()
    
    getSQL = "SELECT vid, name FROM taxonomy_vocabulary WHERE hierarchy = 1 ORDER BY vid"
    
    debugOutputFileHandle.write("getVocabularies sql statement: " + str(getSQL) + ENDL)
    debugOutputFileHandle.flush()
    cursor.execute(getSQL)
    vocabularies = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return vocabularies

def getTaxonomyTopLevel(debugOutputFileHandle, vocabularyID):
    conn = MySQLdb.connect(host=dbHost, user=dbUser, passwd=dbPassword, database=dbDatabase, port=dbPort)
    cursor = conn.cursor()
    
    getSQL = "SELECT taxonomy_term_data.tid, name "
    getSQL = getSQL + "FROM taxonomy_term_data "
    getSQL = getSQL + "LEFT JOIN taxonomy_term_hierarchy "
    getSQL = getSQL + "ON (taxonomy_term_data.tid = taxonomy_term_hierarchy.tid) "
    getSQL = getSQL + "WHERE vid = " + str(vocabularyID) + " "
    getSQL = getSQL + "AND taxonomy_term_hierarchy.parent = 0 "
    getSQL = getSQL + "ORDER BY name, weight, taxonomy_term_data.tid"
    
    debugOutputFileHandle.write("getTaxonomy sql statement: " + str(getSQL) + ENDL)
    debugOutputFileHandle.flush()
    cursor.execute(getSQL)
    taxonomyTopLevels = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return taxonomyTopLevels

def printChildren(debugOutputFileHandle, outputFileHandle, vocabularyID, childTID, depth):
    conn = MySQLdb.connect(host=dbHost, user=dbUser, passwd=dbPassword, database=dbDatabase, port=dbPort)
    cursor = conn.cursor()
    
    getSQL = "SELECT taxonomy_term_data.tid, name "
    getSQL = getSQL + "FROM taxonomy_term_data "
    getSQL = getSQL + "LEFT JOIN taxonomy_term_hierarchy "
    getSQL = getSQL + "ON (taxonomy_term_data.tid = taxonomy_term_hierarchy.tid) "
    getSQL = getSQL + "WHERE vid = " + str(vocabularyID) + " "
    getSQL = getSQL + "AND taxonomy_term_hierarchy.parent = " + str(childTID) + " "
    getSQL = getSQL + "ORDER BY name, weight, taxonomy_term_data.tid"
    
    debugOutputFileHandle.write("getTaxonomy sql statement: " + str(getSQL) + ENDL)
    debugOutputFileHandle.flush()
    cursor.execute(getSQL)
    children = cursor.fetchall()
    cursor.close()
    conn.close()

    for child in children:
        childTID = child[0]
        childTermName = child[1]
        outputFileHandle.write('-' * depth + childTermName + ENDL)
        outputFileHandle.flush()
        printChildren(debugOutputFileHandle, outputFileHandle, vocabularyID, childTID, depth+1)

debugOutputFileHandle = open('output\\' + currentWebsite + '\\Logs\\debug.log', mode='w')
vocabularies = getVocabularies(debugOutputFileHandle)
for vocabulary in vocabularies:
    currVocabularyID = vocabulary[0]
    currVocabularyName = vocabulary[1]
    outputFileHandle = open('output\\' + currentWebsite + '\\' + currVocabularyName + "_taxonomy.txt", mode='w')
    taxonomyTopLevels = getTaxonomyTopLevel(debugOutputFileHandle, currVocabularyID)
    flushPrintFiles(debugOutputFileHandle, outputFileHandle)
    for taxonomyTopLevel in taxonomyTopLevels:
        currTermTID = taxonomyTopLevel[0]
        currTermName = taxonomyTopLevel[1]
        outputFileHandle.write(currTermName + ENDL)
        printChildren(debugOutputFileHandle, outputFileHandle, currVocabularyID, currTermTID, 1)
        flushPrintFiles(debugOutputFileHandle, outputFileHandle)
    outputFileHandle.close()
debugOutputFileHandle.close()

