import requests
import json
import asyncio
import os,time
from datetime import datetime
from requests.api import get
import functools
version="1.37.0"
aliases=json.loads(open("aliases.json","r").read())
temp=[]
pricecache={}
for a in aliases:
    r=a
    r["name"]=r["name"].lower()
    temp.append(r)

aliases=temp
acces_token=""
def getId(name):
    for i in aliases:
        if(i["name"]==name):
            return i["id"]
    return -1
    
def getHeader():
    global acces_token
    header={"Authorization": "bearer "+acces_token,"Application":"Pokemon TCG Discord Bot"}
    return header

def getAccesToken():
    data="grant_type=client_credentials&client_id=7c270ea4-5c51-402d-be29-d264151c797b&client_secret=bfa29f7c-037d-49ca-b65e-f114e5fec5e5"
    header="application/x-www-form-urlencoded"
    result=requests.post("https://api.tcgplayer.com/token",data=data)
    result=json.loads(result.content.decode("utf-8"))
    return result["access_token"]

def getPrice(sku):
    url="https://api.tcgplayer.com/pricing/marketprices/"+str(sku)
    result=requests.get(url,headers=getHeader())
    try:
        price=round(int(json.loads(result.text)["results"][0]["price"])*10)
        return price
    except:
        #print("Sku: "+str(sku))
        #print("result: "+result.text)
        return 1000

def getBoosterPrice(name):
    if("promo" in name):
        return 5000
    if(name in pricecache):
        difference=datetime.utcnow()-pricecache[name][1]
        if(difference.days==0):
            return pricecache[name][0]
    url= "https://api.tcgplayer.com/catalog/products"
    querystring={"categoryId":"3","groupId": getId(name),"productTypes":"Sealed Products", "limit":"100","includeSkus":"true"}
    result=requests.get(url,headers=getHeader(),params=querystring)
    result=json.loads(result.content.decode("utf-8"))
    for i in result["results"]:
        if("Pack" in  i["name"]):
            price=getPrice(i["skus"][0]["skuId"])
            pricecache[name]=[price,datetime.utcnow()]
            return price
    return 1000
def getSets():
    url = "https://api.tcgplayer.com/catalog/categories/3/groups"
    querystring = {"limit":"100","offset":100}
    result = requests.get(url,headers=getHeader(),params=querystring)
    text='['
    for i in json.loads(result.text)["results"]:
        text+='{\n'
        text+='"id":"'+str(i["groupId"])+'",\n'+'"name":"'+str(i["name"])+'"\n'
        text+='},\n'
    text+=']'
    open("aliases2.json","w").write(text)

def testSets():
    sets=os.listdir(r"cards")
    count=0
    names=[]
    wrong=[]
    for i in sets:
        names.append(i.replace(".json",""))
    for i in names:
        count+=1
        print("Doing Set: "+i+"  "+str(count)+"/"+str(len(names)))
        if(getBoosterPrice(i)==None):
            print("Failed! "+i)
            wrong.append(i)
        #input("Press enter to continue: ")
    print(wrong)

def getSets():
    sets=os.listdir(r"cards")
    count=0
    names=[]
    pricecache={}
    for i in sets:
        names.append(i.replace(".json",""))
    for i in names:
        count+=1
        print("Doing Set: "+i+"  "+str(count)+"/"+str(len(names)))
        price=getBoosterPrice(i.lower())
        if(price==None):
            print("Failed! "+i+", setting to 100")

        #input("Press enter to continue: ")
    print(pricecache)
    
async def getCardPrice(id):
    if(id in pricecache):
        difference=datetime.utcnow()-pricecache[id][1]
        if(difference.days==0):
            return pricecache[id][0]
            
    try:
        header={"X-Api-Key":api_key}
        loop = asyncio.get_event_loop()
        future =  loop.run_in_executor(None, functools.partial(requests.get,url="https://api.pokemontcg.io/v2/cards?q=id:"+id,headers=header))
        result = await future
        result=json.loads(result.text)
        result=result["data"][0]["tcgplayer"]["prices"]
        for i in result:
            price=round(float(result[i]["market"])*5)
            pricecache[id]=[price,datetime.utcnow()]
            return str(int(price))
    except Exception as e:
        print(e)
        return "1"
    return "1"

def getCardPriceBlocking(id):
    if(id in pricecache):
        difference=datetime.utcnow()-pricecache[id][1]
        if(difference.days==0):
            return pricecache[id][0]
            
    try:
        header={"X-Api-Key":api_key}
        result = requests.get(url="https://api.pokemontcg.io/v2/cards?q=id:"+id,headers=header)
        result=json.loads(result.text)
        result=result["data"][0]["tcgplayer"]["prices"]
        for i in result:
            price=round(float(result[i]["market"])*5)
            pricecache[id]=[price,datetime.utcnow()]
            return str(int(price))
    except Exception as e:
        print(e)
        return "1"
    return "1"

acces_token=getAccesToken()
api_key="c7bcd5e4-c594-4e99-88ff-c9e64ad14909"
