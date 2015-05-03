#!/usr/bin/python
import json
import re
import time


usedBlocks = set()

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
    print "Checking device Id ......."
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
        print "Device ID correct\n"
    else:
        print "Incorrect Device ID\n"



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
  print "ADDED BLOCK - " + blockNumber
  
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
                print "checking DIRECTORY ... %s" %(linkdetails[1])
                DirectoryTraversal(linkdetails[2])
        if linkdetails[0] == 'f':
                print "checking FILE..... %s" %(linkdetails[1])
                mFile =  json.loads(ReadFile(linkdetails[2]))
                #------------- Check times --------------------------------
                if float(time.time()) - float(mFile['ctime']) < 0 :
                    print "\tInvalid ctime"
                if float(time.time()) - float(mFile['atime']) < 0 :
                    print "\tInvalid atime"
                if float(time.time()) - float(mFile['mtime']) < 0 :
                    print "\tInvalid mtime"

                mBlock = str(mFile['location'])
                if int(mFile['indirect']) == 1:
                    if checkArray(mBlock) == False:
                        print "Invalid indirect value/Incorrect location entry"
                if int(mFile['indirect']) == 0:
                    ReadFile(mBlock)

# -------------------------------- CHECK IF ARRAY --------------------------------------
def checkArray(blockNumber):
    result = True
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
            result = False
            blockfile.close()
            return result

    blockfile.close()
    
    return result

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

# ------------------------------- FREE BLOCK MANAGEMENT ------------------------------------
def getFreeBlocks():
    blockList = []
    for i in xrange(1,26):
        temp = map(int,ReadBlocks(str(i)).strip().split(","))
        blockList = blockList + temp
    #print blockList

def addToUsedBlocks(blockNumber):
    global usedBlocks
    usedBlocks.add(blockNumber)

#------------- Call check methods one after the other ------------------------------------------
print "\n ----------------------- File Check Results -----------------\n"

checkDeviceID()
print "checking DIRECTORY ... %s" %("root")
DirectoryTraversal("26")
getFreeBlocks()
print usedBlocks






