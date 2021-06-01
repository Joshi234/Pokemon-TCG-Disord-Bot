import requests,json

def getNewVotes(countOld):
    result=requests.get("https://top.gg/api//bots/806943204830216243/votes").content
    result=json.loads(result)
    print(result)
    value=[]
    if(len(result)>countOld):
        newLen=len(result)-countOld
        for i in range(newLen):
            value.append(result[i])
    count=len(result)
    saveCount()
    return value

def getCount():
    return count
    
def saveCount():
    global count
    open("vote_count.txt","x").write(str(count))

def loadCount():
    global count
    try:
        count = int(open("vote_count.txt","r").read())
    except:
        count=0
        saveCount()

loadCount()
