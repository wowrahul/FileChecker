#!/usr/bin/python
import json
import re
import time


usedBlocks = set()
freeBlocks = set()

# Get JSON representation for a directory entry from a fusedata.# block
def getjsondir(string):

    dirDictionary = None

    try:

        startindex =  string.rfind("filename_to_inode_dict:")
        filelist = string[startindex:]
        directoryInfo = string[:startindex]

        filelist = filelist.strip()[:-1]
        jsonString =  directoryInfo.strip()[:-1] + "}"

        jsonString = re.sub(r"{\s*'?(\w)", r'{"\1', jsonString)

        jsonString = re.sub(r",\s*'?(\w)", r',"\1', jsonString)

        jsonString = re.sub(r"(\w)'?\s*:", r'\1":', jsonString)

        jsonString = re.sub(r":\s*'(\w+)'\s*([,}])", r':"\1"\2', jsonString)

        dirDictionary =  json.loads(jsonString)
        fileKeys = filelist.split(":",1)

        dirDictionary[fileKeys[0].strip()] = fileKeys[1].strip()
    except:
        dirDictionary = None
    return dirDictionary

# Get JSON entry for the SuperBlock
def getjson(string):

    jsonString = string
    jsonString = re.sub(r"{\s*'?(\w)", r'{"\1', jsonString)
    jsonString = re.sub(r",\s*'?(\w)", r',"\1', jsonString)
    jsonString = re.sub(r"(\w)'?\s*:", r'\1":', jsonString)
    jsonString = re.sub(r":\s*'(\w+)'\s*([,}])", r':"\1"\2', jsonString)
    return jsonString

# ------------------------------------ CHECK DEVICE ID ---------------------------------
def checkDeviceID():
    print "Checking DEVICE ID ..."
    result = "true"
    blockfile = open("FS/fusedata.0", "r")
    fileConent = blockfile.read()
    contents = getjson(fileConent.strip())
    try:
        devId =  int(json.loads(contents)['devId'])
    except:
        print "Invalid Device ID"
        return

    blockfile.close()
    if devId == 20:
        print "\tDevice ID correct\n"
    else:
        print "\tIncorrect Device ID\n"



# Check . and .. entry in parent directory
def checkInParent(parentBlock,currentBlock):
    parent = readDirectory(parentBlock)
    if  parent == None:
        return False
    else:
        return True
    

# --------------------------------- TRAVERSE DIRECTORIES ---------------------------------
def DirectoryTraversal(blockNumber):

  directory  = 	readDirectory(blockNumber)

  addToUsedBlocks(blockNumber)
  #print "ADDED BLOCK - " + blockNumber
  
#------------- Check times --------------------------------
  if float(time.time()) - float(directory['ctime']) < 0 :
    print "\tInvalid ctime"
  if float(time.time()) - float(directory['atime']) < 0 :
    print "\tInvalid atime"
  if float(time.time()) - float(directory['mtime']) < 0 :
    print "\tInvalid mtime"

#------------  Check Links --------------------------------	

  links =  directory['filename_to_inode_dict'][1:-1].split(",")

  #check link count
  if len(links) != int(directory['linkcount']):
        print "Invalid linkcount"

  
  foundsingle = False
  founddouble = False
  for link in links:
        linkdetails = link.strip().split(":")
        # check for . and ..
        if linkdetails[0] == 'd':
            if linkdetails [1] == '.':
                    foundsingle = True
                    if checkInParent(linkdetails[2],blockNumber) == False:
                        print "\tInvalid block for ."

            if linkdetails [1] == '..':
                founddouble = True
                if checkInParent(linkdetails[2],blockNumber) == False:
                        print "\tInvalid block for .."

  if founddouble == False:
    print "No entry for .."
  if foundsingle == False:
    print "No entry for ."

  for link in links:
        linkdetails = link.strip().split(":")
        # "Traverse through sub directories"
        if linkdetails[0] == 'd':
            if linkdetails [1] not in ['.','..']:
                print "\nchecking DIRECTORY ... %s" %(linkdetails[1])
                DirectoryTraversal(linkdetails[2])
        if linkdetails[0] == 'f':
                print "\nchecking FILE ... %s" %(linkdetails[1])
                try:
                    mFile =  json.loads(ReadFile(linkdetails[2]))
                except Exception, e:
                    print "\tError in reading file info"
                    continue
                
                #------------- Check times --------------------------------
                if float(time.time()) - float(mFile['ctime']) < 0 :
                    print "\tInvalid ctime"
                if float(time.time()) - float(mFile['atime']) < 0 :
                    print "\tInvalid atime"
                if float(time.time()) - float(mFile['mtime']) < 0 :
                    print "\tInvalid mtime"
                mBlock = str(mFile['location'])

                if int(mFile['indirect']) == 1:
                    arrayCount = checkArray(mBlock)
                    if arrayCount == -1:
                        print "\tInvalid indirect value/Incorrect location entry"
                    else:
                        if (checkSize(arrayCount,int(mFile['indirect']) ,int(mFile['size']))) == False:
                            print "\t Invalid Size of file"
                if int(mFile['indirect']) == 0:
                    if (checkSize(1,int(mFile['indirect']) ,int(mFile['size']))) == False:
                            print "\t Invalid Size of file"
                    try:
                        ReadFile(mBlock)
                    except Exception, e:
                        print "\tError in reading file"
                        continue

                   


# -------------------------------- CHECK SIZE ------------------------------------------
def checkSize(blockCount, indirectValue, size):
    result = True
    blocksize = 4096
    if indirectValue == 0:
        if size <= 0 or size >= blocksize:
            return False
    if indirectValue == 1:
          if size >= (blocksize * blockCount):
            return False
          if size <= (blocksize * (blockCount - 1) ):
            return False
          

# -------------------------------- CHECK IF ARRAY --------------------------------------
def checkArray(blockNumber):
    result = 0
    blockfile = open("FS/fusedata." + blockNumber, "r")
    addToUsedBlocks(blockNumber)
    fileContent = blockfile.read()
    #mFile = fileContent.strip()
    blocks = fileContent.strip().split(",")
    for block in blocks:
        try: 
            iblock = int(block)
            addToUsedBlocks(block)

        except:
            result = -1
            blockfile.close()
            #return result

    blockfile.close()
    
    if result == -1:
        return -1
    else:
        return len(blocks)

# --------------------------------- READ DIRECTORY ---------------------------------------
def readDirectory(blockNumber):
    blockfile = open("FS/fusedata." + blockNumber, "r")
    fileConent = blockfile.read()
    directory = getjsondir(fileConent.strip())
    blockfile.close()
    return directory

# --------------------------------- READ FILE ---------------------------------------------	
def  ReadFile(blockNumber):
    
    blockfile = open("FS/fusedata." + blockNumber, "r")
    fileContent = blockfile.read()
    mFile = getjson(fileContent.strip())
    blockfile.close()
    addToUsedBlocks(blockNumber)
    return mFile

# ------------------------------- READ BLOCKS LIST ---------------------------------------
def  ReadBlocks(blockNumber):
    blockfile = open("FS/fusedata." + blockNumber, "r")
    fileContent = blockfile.read()
    blockfile.close()
    addToUsedBlocks(blockNumber)
    return fileContent

# ------------------------------- BLOCK MANAGEMENT ------------------------------------
def getFreeBlocks():
    blockList = []
    for i in xrange(1,26):
        temp = map(int,ReadBlocks(str(i)).strip().split(","))
        blockList = blockList + temp

    global freeBlocks
    for block in blockList:
        freeBlocks.add(block)

def addToUsedBlocks(blockNumber):
    global usedBlocks
    usedBlocks.add(int(blockNumber))    

def checkBlocks():
    print "\nChecking BLOCKS ... "
    isError = False
    try:
        commonBlocks = freeBlocks.intersection(usedBlocks)
        if len(commonBlocks) > 0:
            print "\tOverlapping free and used blocks : " 
            for block in commonBlocks:
                print "\t%s" %(block)
            isError = True
    except Exception, e:
        print "\tError in blocks list"
        isError = True

    if  len(freeBlocks | usedBlocks) != 10000:
        print "\tNot all free blocks are on the list. Total number of blocks (Free and Used ) found : " + str(len(freeBlocks | usedBlocks)) + ". The total should be 10000. \n"
        isError = True

    if isError == False:
        print "\tNo errors found in blocks list\n"

    print usedBlocks
   

#------------- Call check methods one after the other ------------------------------------------
print "\n ----------------------- File System Check Results -----------------\n"

checkDeviceID()
global usedBlocks
usedBlocks.add(0)
print "checking DIRECTORY ... %s" %("root")
DirectoryTraversal("26")
getFreeBlocks()
checkBlocks()






