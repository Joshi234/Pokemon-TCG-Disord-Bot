import database
import json
import discord
packsopenedAchievements =        [3,  10 ,50, 100,200,300 ,400 ,500, 750, 1000,2000]
packsopenedAchievementsRewards = [100,200,300,500,750,1000,1500,2000,2500,5000,"badge"]
cardsoldAchievements =           [10, 50,200,500,1000,2000,4000,8000,10000]
cardsoldRewards =                [50,100,200,300,500, 750 ,1000,2000,"badge"]
levels =                         [100,250,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,12000,14000,16000,18000,20000,25000,30000,35000,40000,45000,50000]
rewardsLevels =                  [100,200,300,400, 500, 750 ,"red",1250,1500,1750,2000,2250,"green" ,2750 , 3000,3500, 4000, "blue",5000,  6000,7000,  8000, 9000, "badge"]
badges = {"cascade" : "<:Cascade_Badge:833053566419730492>", "volcano": "<:Volcano_Badge:833053501961666560>", "earth" : "<:Earth_Badge:833053489244012565>","marsh" : "<:Marsh_Badge:833053514119774260>", "rainbow" : "<:Rainbow_Badge:833053536677396530>","soul" : "<:Soul_Badge:833053526070394900>", "thunder" : "<:Thunder_Badge:833053556067401789>", "boulder" : "<:Boulder_Badge:828438440056061992>"}
#Used : cascade
def loadAchievement(userId):
    try:
        return json.loads(database.getStats(userId))
    except:
        return getDefaultData()

def getDefaultData():
    return json.dumps({"packsopened" : 0,"cardsold" : 0})

async def modifyStats(ctx,userId,key,value):
    temp = loadAchievement(userId)
    old = temp[key]
    temp[key] = value
    database.updateStats(userId,json.dumps(temp))
    await checkForAchievement(ctx,userId,key,value, old)

async def addToStats(ctx, userId,key,value):
    temp = loadAchievement(userId)
    old = temp[key]
    temp[key] += value
    database.updateStats(userId,json.dumps(temp))
    await checkForAchievement(ctx,userId,key,temp[key],old)

def addBadge(userId,badge):
    badgesTemp = json.loads(database.getData(userId, database.Rows.BADGE))
    badgesTemp.append(badges[badge])
    print(badgesTemp)
    database.editData(userId,database.Rows.BADGE,json.dumps(badgesTemp))

async def sendAchievementdm(user, message, reward):
    embed = discord.Embed(colour= discord.Colour.blue())
    embed.set_author(name = 'Achievements', url="https://joshi234.github.io/",icon_url="https://images.discordapp.net/avatars/806943204830216243/9a97a37d4fe09317b69b24d9db434a92.png?size=128")
    embed.add_field(name = "Achievement got!",value=message)
    embed.add_field(name = "Reward:", value=reward)
    await user.send(embed=embed)

async def checkForAchievement(ctx, userId,key, value ,oldvalue):
    if(key == "packsopened"):
        values = packsopenedAchievements
        rewards  = packsopenedAchievementsRewards
        badge = "cascade"
        message = "Packs"
        premessage = "Buy "
    if(key == "cardsold"):
        values = cardsoldAchievements
        rewards = cardsoldRewards
        badge = "volcano"
        message = "Cards"
        premessage = "Sell "
    for i in range(len(values)):
        if values[i] > oldvalue:
            if(values[i] <= value):
                reward = str(rewards[i])
                try: 
                    int(reward)
                    database.addToData(userId, database.Rows.BALANCE,reward)
                    await sendAchievementdm(ctx, premessage + str(values[i]) +" "+message, reward + " Pokecoins")
                except:
                    if(reward == "badge"):
                        addBadge(userId, badge)
                        await sendAchievementdm(ctx, premessage + str(values[i]) +" "+message, badge + " Badge")

    return "", ""

async def checkForXp(ctx, userId,  value, oldvalue):
    badge = "rainbow"
    for i in range(len(levels)):
        if levels[i] > oldvalue:
            if(levels[i] <= value):
                reward = str(rewardsLevels[i])
                try:
                    int(reward)
                    database.addToData(userId, database.Rows.BALANCE,reward)
                    await sendAchievementdm(ctx, "Reach Level " + str(i+1)  , reward + " Pokecoins") 
                except:
                    if(reward == "badge"):
                        addBadge(userId, badge)
                        await sendAchievementdm(ctx, "Reach Level " + str(i+1)  , badge + " Badge")

                    else:
                        colours = json.loads(database.getData(userId,database.Rows.SPECIALITEMS))
                        colours["profileColours"].append(reward)
                        database.editData(userId,database.Rows.SPECIALITEMS,json.dumps(colours))
                        await sendAchievementdm(ctx, "Reach Level " + str(i+1)  , reward + " Profile Colour")

def getLevel(level):
    try:
        for i in range(len(levels)):

            if(level < levels[i+1] and level > levels[i]):
                return i+1,convertRewardToString(rewardsLevels[i+1])
    except:
        return len(levels),"You are max Level"

def convertRewardToString(reward):
    try: 
        int(reward)
        return str(reward) + " Pokecoins"
    except:
        if(reward == "badge"):
            return "Badge"
        else:
            return "Profile Colour "+reward
