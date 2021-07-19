
import sqlite3
from enum import Enum
import json
from discord import user
conn = sqlite3.connect("database.db",check_same_thread=False)
c=conn.cursor()
historyConn = sqlite3.connect("history.db",check_same_thread=False)
historyC = historyConn.cursor()
version="4"
defaultPacks=["Team Up","Vivid Voltage","Sword & Shield","Celestial Storm","Sun & Moon"]

class Rows(Enum):
    BALANCE=1
    COLLECTION=2
    XP=3
    NAME=4
    BADGE=5
    SPECIALITEMS=6
    PROFILECOLOUR=7
    GEMS=8
    BATTLEPASSLEVEL=9

class HistoryID(Enum):
    PACKBOUGHT = 1
    SOLD = 2
    CARDBOUGHT = 3
    SELLMASS = 4
    EDITDATA = 5
    ADDTODATA = 6
    SPECIALITEM = 7

def addData(userId,bal,collection,xp,name, badges,specialItems, profileColour,gems, bpLevel):
    '''Inserts a new column into the DataBase'''
    c.execute("INSERT INTO DataBase VALUES(?,?,?,?,?,?,?,?,?,?)",(str(userId),str(bal),str(collection),str(xp),str(name),str(badges),str(specialItems),int(profileColour),int(gems),int(bpLevel),))
    conn.commit()

def createNewDefaultData(userId):
    addData(userId,0,"[]",0,"", json.dumps([]),json.dumps({"profileColours":[]}),0,0,0)
    for ie in defaultPacks:
        addSpecialItem(userId,"packs",ie)
def checkNameMigrated(userId,name):
    c.execute("SELECT * FROM DataBase WHERE userId=?",(userId,))
    if(c.fetchone()[4]==""):
        editData(userId,Rows.NAME,name)

def getData(userId,row):
    '''Gets Date with userId and a row'''
    if(getDataCreated(userId)):
        c.execute('SELECT * FROM DataBase WHERE userId=?',(userId,))
        return c.fetchone()[row.value]
    else:
        createNewDefaultData(userId)
        return getData(userId,row)
def getTop():
    c.execute("SELECT xp,name FROM DataBase ORDER BY xp DESC LIMIT 10")
    return c.fetchmany(10)

def createDB():
    '''Creates a DataBase'''
    try:
        c.execute('''CREATE TABLE Stats
    (userId TINYTEXT, stats LONGTEXT )''')
        c.execute('''CREATE TABLE Issued
    (cardId TEXT,count TEXT )''')
        c.execute('''CREATE TABLE DataBase
        (userId TINYTEXT,balance  INTEGER ,collection LONGTEXT,xp INTEGER ,name TINYTEXT, badges TEXT, specialitems LONGTEXT, profileColour INT, gems INTEGER  )''')
    except:
        print("Table already exists")

def createHistoryDB():
    '''Creates a DataBase'''
    try:
        historyC.execute('''CREATE TABLE History
        (userId TINYTEXT, historyId INTEGER, notes LONGTEXT )''')

    except:
        print("Table already exists")

createHistoryDB()
def editData(userId,row,value):
    '''Edits a column in the DataBase'''
    if(row.value==1):
        c.execute("UPDATE DataBase SET balance=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value==2):
        c.execute("UPDATE DataBase SET collection=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value==3):
        c.execute("UPDATE DataBase SET xp=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value==4):
        c.execute("UPDATE DataBase SET name=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value==5):
        c.execute("UPDATE DataBase SET badges=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value==6):
        c.execute("UPDATE DataBase SET specialitems=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value==7):
        c.execute("UPDATE DataBase SET profileColour=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value == 8):
        c.execute("UPDATE DataBase SET gems=? WHERE userId=?",(str(value),str(userId),))
    elif(row.value == 9):
        c.execute("UPDATE DataBase SET battlePassLever=? WHERE userId=?",(str(value),str(userId),))
    else:
        print("Unknown Row")
    conn.commit()

def addToData(userId,row,value):
    '''Does an addition with the current value of a column'''
    amount=int(getData(userId,row))
    if(row.value==1):
        if(str(value)!="10"):
            insertHistory(HistoryID.ADDTODATA,userId,"Added money: "+str(value))
        c.execute("UPDATE DataBase SET balance=? WHERE userId=?",(str(amount+int(value)),str(userId),))
    elif(row.value==2):
        c.execute("UPDATE DataBase SET collection=? WHERE userId=?",(str(amount+ int(value)),str(userId),))
    elif (row.value==3):
        insertHistory(HistoryID.ADDTODATA,userId,"Added xp: "+str(value))
        c.execute("UPDATE DataBase SET xp=? WHERE userId=?",(str(amount+ int(value)),str(userId),))
    elif (row.value==8):
        insertHistory(HistoryID.ADDTODATA,userId,"Added gems: "+str(value))
        c.execute("UPDATE DataBase SET gems=? WHERE userId=?",(str(amount+  int(value)),str(userId),))
    elif (row.value==9):
        insertHistory(HistoryID.ADDTODATA,userId,"Added battlePassLevel: "+str(value))
        c.execute("UPDATE DataBase SET battlePassLevel=? WHERE userId=?",(str(amount+  int(value)),str(userId),))
    else:
        print("Unknown Row")
    conn.commit()

def getDataCreated(userId):
    '''Return True when the Data is already in the Table and False if not'''
    c.execute("SELECT EXISTS(SELECT 1 FROM DataBase WHERE userId=?)",(userId,))
    
    if(c.fetchone()[0]==1):
        return True
    else:
        return False

def addIssued(cardId):
    c.execute("SELECT EXISTS(SELECT 1 FROM Issued WHERE cardId=?)",(cardId,))
    if(c.fetchone()[0]==1):
        c.execute('SELECT * FROM Issued WHERE cardId=?',(cardId,))
        count=int(c.fetchone()[1])
        count+=1
        c.execute("UPDATE Issued SET count=? WHERE cardId=?",(str(count),str(cardId),))
        conn.commit()
        return count
    else:
        c.execute("INSERT INTO Issued VALUES(?,?)",(str(cardId),str(1),))
        conn.commit()
        return 1

def updateStats(userId,data):
    if(getStatsCreated(userId)):
        c.execute("UPDATE Stats SET stats=? WHERE userId=?",(data,str(userId)))
    else:
        c.execute("INSERT INTO Stats VALUES(?,?)",(str(userId),data,))
    conn.commit()

def getStats(userId):
    if(getStatsCreated(userId)):
        c.execute('SELECT stats FROM Stats WHERE userId=?',(str(userId),))
        conn.commit()
        return c.fetchone()[0]
    else:
        c.execute("INSERT INTO Stats VALUES(?,?)",(str(userId),json.dumps({"packsopened" : 0,"cardsold" : 0, "achievementsreached" : json.dumps({})}),))
        conn.commit()
        return getStats(userId)

def getStatsCreated(userId):
    c.execute("SELECT EXISTS(SELECT 1 FROM Stats WHERE userId=?)",(userId,))
    
    if(c.fetchone()[0]==1):
        return True
    else:
        return False

def getCardsCollected(userId):
    return len(json.loads(getData(userId,Rows.COLLECTION)))

def getIssued(cardId):
    c.execute("SELECT EXISTS(SELECT 1 FROM Issued WHERE cardId=?)",(cardId,))
    if(c.fetchone()[0]==1):
        c.execute('SELECT * FROM Issued WHERE cardId=?',(cardId,))
        count=int(c.fetchone()[1])
        return count
    else:
        return 0

createDB()

def migrate():
    collection=json.loads(open("collection.json","r").read())
    bal=json.loads(open("bal.json","r").read())
    for i in bal:
        try:
            balance=bal[str(i)]
        except:
            balance=0
        try:
            col=json.dumps(collection[str(i)])
        except:
            col="[]"
        addData(i,balance,col)
    count=json.loads(open("counts.json","r").read())
    for i in count:
        for ie in range(count[i]):
            addIssued(i)


def updateTable(version):
    if(version=="2"):
        data=conn.execute("select * from DataBase")
        list=data.fetchall()
        updated=[]
        for i in list:
            temp=[i[0],i[1],i[2],0,"",i[3]]
            temp[1]=int(temp[1])
            temp[4]="2"
            updated.append(temp)
        c.execute("DROP TABLE DataBase")
        c.execute('''CREATE TABLE DataBase
        (userId TINYTEXT,balance  INTEGER ,collection LONGTEXT,xp INTEGER ,name TINYTEXT,version TINYTEXT )''')
        for i in updated:
            addData(i[0],i[1],i[2],i[3],"")
    elif (version=="3"):
        data=conn.execute("select * from DataBase")
        list=data.fetchall()

        c.execute("DROP TABLE DataBase")
        c.execute('''CREATE TABLE DataBase
        (userId TINYTEXT,balance  INTEGER ,collection LONGTEXT,xp INTEGER ,name TINYTEXT, badges TEXT, specialitems LONGTEXT, profileColour INT )''')
        for i in list:
            addData(i[0],i[1],i[2],0,i[4], json.dumps([]),json.dumps({"profileColours":["default"]}),0)
    elif (version=="4"):
        data=conn.execute("select * from DataBase")
        list=data.fetchall()

        c.execute("DROP TABLE DataBase")
        c.execute('''CREATE TABLE DataBase
        (userId TINYTEXT,balance  INTEGER ,collection LONGTEXT,xp INTEGER ,name TINYTEXT, badges TEXT, specialitems LONGTEXT, profileColour INT, gems INTEGER )''')
        defaultPacks=["Team Up","Vivid Voltage","Sword & Shield","Celestial Storm","Sun & Moon"]
        for i in list:
            addData(i[0],i[1],i[2],i[3],i[4], i[5],i[6],i[7],0)
            for ie in defaultPacks:
                addSpecialItem(i[0],"packs",ie)
    elif (version=="5"):
        data=conn.execute("select * from DataBase")
        list=data.fetchall()

        c.execute("DROP TABLE DataBase")
        c.execute('''CREATE TABLE DataBase
        (userId TINYTEXT,balance  INTEGER ,collection LONGTEXT,xp INTEGER ,name TINYTEXT, badges TEXT, specialitems LONGTEXT, profileColour INT, gems INTEGER, battlePassLevel INTEGER )''')
        for i in list:
            addData(i[0],i[1],i[2],i[3],i[4], i[5],i[6],i[7],i[8],0)

def insertHistory(historyId, userId, notes):
    historyC.execute("INSERT INTO History VALUES(?,?,?)",(str(userId),historyId.value,str(notes)))
    historyConn.commit()

def getSpecialItem(userId,key):
    try:
        data = json.loads(getData(userId,Rows.SPECIALITEMS))
        return data[key]
    except:
        return []
def addSpecialItem(userId,key,value):
    data = json.loads(getData(userId,Rows.SPECIALITEMS))
    insertHistory(HistoryID.SPECIALITEM,userId,"Key: "+str(key)+" Value: "+str(value))
    try:
        data[key].append(value)
    except:
        data[key] = [value]
    editData(userId,Rows.SPECIALITEMS,json.dumps(data))
