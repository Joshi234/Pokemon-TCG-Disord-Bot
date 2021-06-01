def parseArgs(text):
    temp=[]
    te=""
    for i in text:
        if(i==" "):
            if(te!=""):
                temp.append(te)
                te=""
        else:
            te+=i
    if(te!=""):
        temp.append(te)
    return temp