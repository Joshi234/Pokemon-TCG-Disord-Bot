import discord
from discord.ext import commands
import asyncio
import json
import os
import random
import time
import traceback
from database import *
from stuff import *
import tcgplayer as tcg
from threading import Thread
from discord_slash import SlashCommand, SlashContext
import datetime
import achievements
import config
version="0.5"
badges = {"cascade" : "<:Cascade_Badge:833053566419730492>", "volcano": "<:Volcano_Badge:833053501961666560>", "earth" : "<:Earth_Badge:833053489244012565>","marsh" : "<:Marsh_Badge:833053514119774260>", "rainbow" : "<:Rainbow_Badge:833053536677396530>","soul" : "<:Soul_Badge:833053526070394900>", "thunder" : "<:Thunder_Badge:833053556067401789>", "boulder" : "<:Boulder_Badge:828438440056061992>"}
changelogText="Added gems\nAdded -show command\nYou unlock packs now by finishing sets\nadd setcompletion command\nAdded website to buy gems to unlock packs"
client = commands.Bot(command_prefix="/")
last_seen={}
slash = SlashCommand(client)
sets=os.listdir(r"cards")
cards={}
cardsSingle = {}
prefix="&"
names=[]
claims={}
id=0
for i in sets:
    names.append(i.replace(".json",""))
    cards[i.replace(".json","").lower()]=json.loads(open(r"cards/"+i,"r",encoding='utf8').read())

for i in cards:
    for ie in cards[i]:
        cardsSingle[ie["id"]]=ie

@client.event
async def on_ready():
    print('Bot is ready.')#tells user, bot is ready

    while(True):
        await client.change_presence(activity= discord.Activity(type=discord.ActivityType.playing, name=names[random.randint(0,len(names)-1)]))#sets status as "Watching:!help"
        
        await asyncio.sleep(random.randint(3600,9000))

def getRandomCard(pack,rarity,packContent):
    global id
    card=cards[pack][random.randint(0,len(cards[pack])-1)]
    try:
        if(rarity=="common" or rarity=="uncommon"):
            if(card["rarity"].lower()==rarity.lower()):
                if(card in packContent):
                    return getRandomCard(pack,rarity,packContent)
                else:    
                    card["card_id"]=id
                    card["issue"]=addIssued(card["id"])
                    id+=1
                    return card
            else:
                return getRandomCard(pack,rarity,packContent)
        else:
            if(card["rarity"].lower()!="common" and card["rarity"].lower()!="uncommon"):
                if(card in packContent):
                    return getRandomCard(pack,rarity,packContent)
                else:
                    if(card["rarity"]!="Rare"):
                        if(random.randint(1,3)==1):
                            card["card_id"]=id
                            card["issue"]=addIssued(card["id"])
                            id+=1
                            return card
                        else:
                            return getRandomCard(pack,rarity,packContent)
                    card["card_id"]=id
                    card["issue"]=addIssued(card["id"])
                    id+=1
                    return card
            else:
                return getRandomCard(pack,rarity,packContent)
    except:
        card["card_id"]=id
        card["issue"]=addIssued(card["id"])
        id+=1
        return card

async def checkIfSetCompleted(user,userId,packName):
    if(packName.lower() not in getSpecialItem(userId,"setComplete")):
        userCards = json.loads(getData(userId,Rows.COLLECTION))
        packName = packName.lower()
        cardPacks=[]
        packIds=[]
        for i in userCards:
            if(i["set"].lower()==packName):
                if (i["id"] not in cardPacks):
                    cardPacks.append(i["id"])
        for i in cards[packName]:
            packIds.append(i["id"])
        if(len(cards[packName]) == len(cardPacks)):
            newSet = getRandomPack(userId)
            addSpecialItem(userId,"packs",newSet)
            addSpecialItem(userId,"setComplete",packName.lower())
            addToData(userId,Rows.GEMS,10)
            await achievements.sendAchievementdm(user,"Complete the set "+packName,"Random new Pack: "+newSet+" & 10 gems")
        return (len(cardPacks)/len(cards[packName]))*100,list(set(packIds) - set(cardPacks))
    else:
        return 100,[]
def getRandomPack(userId):
    packs = getSpecialItem(userId,"packs")
    possiblePacks = []
    for i in names:
        if(i.lower() not in packs):
            possiblePacks.append(i)
    return possiblePacks[random.randint(0,len(possiblePacks)-1)]

async def buy_packs(messageRec,author,skipPack=False,messagePack=None,content=None):
    global collection
    
    userId=str(author.id)
    packs = getSpecialItem(userId,"packs")
    for i in range(len(packs)):
        packs[i] = packs[i].lower()
    loadCollection()
    msgSure=None
    cardspulled=[]
    skip=False
    if(skipPack):
        skip=True
    if(messagePack==None):
        if("skip" in content):
            skip=True
    def checkRecSure(emoji,user):

        return user == author and emoji.message.id == msgSure.id
    def checkRec(emoji,user):
        return user == author and emoji.message.id == message.id
    try:
        if(messagePack!=None):
            if(messagePack in packs):
                pack=messagePack
            else:
                1/0
        else:
            if(content.replace(prefix+"buy ","").replace(" skip","").lower() in packs):
                pack=content.replace(prefix+"buy ","").replace(" skip","").lower()
            else:
                1/0
    except Exception as e:
        print(e)
        await messageRec.send("Please select your pack:")
        
        def checkd(msg):
            return msg.author == author

        msg = await client.wait_for("message",check=checkd, timeout=25)#allows user 15 seconds to respond
        try:
            if(msg.content.lower() in packs):
                pack=msg.content.lower()
            else:
                1/0
        except:
            await messageRec.send("Unknown booster pack")
            return
    if(skip==False):
        price=tcg.getBoosterPrice(pack)
        msgSure = await messageRec.send("One pack costs "+str(price)+" pokecoins, are you sure you want to buy it?")
        await msgSure.add_reaction("☑️")
        reaction, user = await client.wait_for("reaction_add",check=checkRecSure,timeout=100)

        if(reaction.emoji=="☑️" and user!=client.user):
            await msgSure.remove_reaction("☑️",client.user)
            await msgSure.remove_reaction("☑️",user)
            try:
                if(int(getData(userId,Rows.BALANCE))<price):
                    await messageRec.send("Not enough pokecoins, vote here to get additional 1000 pokecoins: https://top.gg/bot/806943204830216243/vote!")
                    return
            except Exception as e:
                await messageRec.send(e)
                return
    else:
        try:
            price=tcg.getBoosterPrice(pack)
            if(int(getData(userId,Rows.BALANCE))<price):
                await messageRec.send("Not enough pokecoins, vote here to get additional 1000 pokecoins: https://top.gg/bot/806943204830216243/vote!")
                return
        except Exception as e:
                await messageRec.send(e)
                return
    addToData(userId,Rows.BALANCE,-1*price)
    xp = getData(userId,Rows.XP)
    xpAdded = round(price/10)

    editData(userId,Rows.XP,xp+xpAdded)
    await achievements.checkForXp(author,userId, xp+xpAdded,xp)
    await achievements.addToStats(author,userId,"packsopened",1)
    insertHistory(HistoryID.PACKBOUGHT,userId,"Pack: "+pack+", Price: "+str(price))
    checkNameMigrated(author.id, author)
    collection=json.loads(getData(userId,Rows.COLLECTION))
    for i in range(0,10):
        if i<6:
            cardspulled.append(getRandomCard(pack,"common",cardspulled))
        elif i<9:
            cardspulled.append(getRandomCard(pack,"uncommon",cardspulled))
        else:
            cardspulled.append(getRandomCard(pack,"",cardspulled))
    for i in cardspulled:
        collection.append(i)
    editData(userId,Rows.COLLECTION,json.dumps(collection))
    saveCollection()
    embed = discord.Embed(colour= discord.Colour.orange())
    embed.set_author(name = 'Pokemon Pack')
    embed.add_field(name = 'Opened', value="1/10", inline= False)
    embed.add_field(name = 'Issued', value=str(cardspulled[0]["issue"])+" / "+str(getIssued(cardspulled[0]["id"])), inline= False)
    embed.add_field(name = 'Price:', value=str(await tcg.getCardPrice(cardspulled[0]["id"])), inline= False)
    embed.set_image(url= cardspulled[0]["imageUrlHiRes"])
    if(msgSure!=None):
        await msgSure.edit(content="", embed=embed)
        message = msgSure
    else:
        message = await messageRec.send(embed=embed)

    #messageCount=await messageRec.channel.send("1/10")
    #messageIssued = await messageRec.channel.send("Issued "+str(cardspulled[0]["issue"])+" / "+str(getIssued(cardspulled[0]["id"])))
    #message = await messageRec.channel.send(cardspulled[0]["imageUrlHiRes"])
    sell_emoji="<:sell:820042237948854277>"
    sold_url="https://www.vhv.rs/dpng/f/418-4187632_sold-sign-png.png"
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")
    await message.add_reaction(sell_emoji)
    sell_emoji_available=True
    sell_reaction=None
    i=0
    try:
        while(True):
            reaction, user = await client.wait_for("reaction_add",check=checkRec,timeout= 100)
            if(author.id==user.id):
                if(reaction.message.id == message.id):
                    if(reaction.emoji=="➡️"):
                        if(i<9):
                            if(sell_emoji_available==False):
                                await message.add_reaction(sell_emoji)

                            i+=1
                            if(cardspulled[i]["imageUrlHiRes"]==sold_url):
                                try:
                                    await message.remove_reaction(sell_reaction,client.user)
                                except:
                                    pass
                            embed = discord.Embed(colour= discord.Colour.orange())
                            embed.set_author(name = pack)
                            embed.add_field(name = 'Opened', value=str(i+1)+"/10", inline= False)
                            embed.add_field(name = 'Issued', value=str(cardspulled[i]["issue"])+" / "+str(getIssued(cardspulled[i]["id"])), inline= False)
                            embed.add_field(name = 'Price:', value=str(await tcg.getCardPrice(cardspulled[i]["id"])), inline= False)
                            embed.set_image(url= cardspulled[i]["imageUrlHiRes"])
                            await message.edit(embed=embed)
                            try:
                                await message.remove_reaction(reaction,user)
                            except:
                                pass
                            if(i==9):
                                    msgSure = await messageRec.send("Do you want to buy another pack for "+str(price)+" pokecoins?")
                                    await msgSure.add_reaction("☑️")
                                    await msgSure.add_reaction("❌")
                                    try:
                                        reaction, user = await client.wait_for("reaction_add",check=checkRecSure,timeout= 10)
                                        if(reaction.emoji=="☑️" and user!=client.user):
                                            await msgSure.delete()
                                            await buy_packs(messageRec,author,skipPack,messagePack,content)
                                        elif(reaction.emoji=="❌" and user!=client.user):
                                            await msgSure.delete()
                                    except:
                                        await msgSure.delete()

                    elif(reaction.emoji=="⬅️"):
                        if(i>0):
                            i-=1
                            if(sell_emoji_available==False):
                                await message.add_reaction(sell_emoji)
                            if(cardspulled[i]["imageUrlHiRes"]==sold_url):
                                try:
                                    await message.remove_reaction(sell_reaction,client.user)
                                except:
                                    pass                            
                            embed = discord.Embed(colour= discord.Colour.orange())
                            embed.set_author(name = 'Pokemon Pack')
                            embed.add_field(name = 'Opened', value=str(i+1)+"/10", inline= False)
                            embed.add_field(name = 'Issued', value=str(cardspulled[i]["issue"])+" / "+str(getIssued(cardspulled[i]["id"])), inline= False)
                            embed.add_field(name = 'Price:', value=str(await tcg.getCardPrice(cardspulled[i]["id"])), inline= False)
                            embed.set_image(url= cardspulled[i]["imageUrlHiRes"])
                            await message.edit(embed=embed)
                            try:
                                await message.remove_reaction(reaction,user)
                            except:
                                pass
                    elif(str(reaction.emoji)==sell_emoji):
                        cardPrice = await tcg.getCardPrice(cardspulled[i]["id"])
                        print("Selling")
                        insertHistory(HistoryID.SOLD,userId,"Card: "+cardspulled[i]["id"]+", Price: "+str(cardPrice))
                        card_id=cardspulled[i]["card_id"]
                        print(card_id)
                        collection=json.loads(getData(userId,Rows.COLLECTION))
                        for ie in collection:
                            if(str(ie["card_id"])==str(card_id)):
                                collection.remove(ie)
                                await achievements.addToStats(author,userId,"cardsold",1)
                                editData(userId,Rows.COLLECTION,json.dumps(collection))
                                addToData(userId,Rows.BALANCE,int(cardPrice))
                                card=cardspulled[i]
                                card["imageUrlHiRes"]=sold_url
                                cardspulled[i]=None
                        try:
                            await message.remove_reaction(reaction,user)
                            await message.remove_reaction(reaction,client.user)
                        except:
                            pass
                        sell_emoji_available=False
                        sell_reaction=reaction
    except Exception as e:
        await message.remove_reaction("➡️",client.user)
        await message.remove_reaction(reaction,client.user)
        await message.remove_reaction("⬅️",client.user)
        if(sell_emoji_available):
            await message.remove_reaction(sell_emoji,client.user)
        print(e)
        return
    print("finished")
#easter egg

async def bal(ctx,id,message,memberName=None):
    global balance
    try:
        args=parseArgs(message)
        argid=args[1].replace("@","").replace(">","").replace("<","").replace("!","")
        if(memberName==None):
            await ctx.send("User has "+str(getData(argid,Rows.BALANCE))+" Pokecoins \nYou have "+str(getData(argid,Rows.GEMS))+" Gems")
        else:
            await ctx.send(memberName+" has "+str(getData(argid,Rows.BALANCE))+" Pokecoins ")
    except Exception as e:
        try:
            await ctx.send("You have "+str(getData(id,Rows.BALANCE))+" Pokecoins\nYou have "+str(getData(id,Rows.GEMS))+" Gems")
        except:
            await ctx.send("You have no pokecoins );")
async def leaderBoard(message):
    leader=getTop()
    embed = discord.Embed(colour= discord.Colour.green())
    temp={}
    r=0
    for i in leader:
        r+=1
        temp[str(r)+". "+str(i[4])]=i[3]
    for i in temp:
        embed.add_field(name=i,value=str(temp[i])+" XP",inline=False)
    await message.send(embed=embed)


@client.command(pass_context = True)
async def ping(ctx):
    await ctx.send(f'Im not too slow... right? {round(client.latency * 1000)}ms')

async def level(ctx, id, user=None):
    embed = discord.Embed(colour= discord.Colour.gold())
    if(user==None):
        xp=getData(id,Rows.XP)
    else:
        xp=getData(user.id,Rows.XP)
    level, nextReward = achievements.getLevel(xp)
    embed.add_field(name="Level",value=str(level),inline=False)
    embed.add_field(name="XP",value=str(xp),inline=False)
    embed.add_field(name="Next Reward",value = nextReward)
    await ctx.send(embed=embed)

async def getCollection(ctx,id):
    await ctx.send("You can find your collection here: https://joshi234.github.io/index.html?id="+str(id))
#help command
async def voteCommand(channel):
    await channel.send("You can vote here: https://top.gg/bot/806943204830216243/vote")

async def sellDuplicates(message, author):
    userId=str(author.id)
    collection=json.loads(getData(userId,Rows.COLLECTION))
    checked={}
    dupes=[]
    for ie in collection:
        if(ie["id"] in checked):
            if(int(ie["issue"])>int(checked[ie["id"]]["issue"])):
                dupes.append(ie)
            else:
                dupes.append(checked[ie["id"]])
                del checked[ie["id"]]
                checked[ie["id"]]=ie
        else:
            checked[ie["id"]]=ie
    embed = discord.Embed(colour= discord.Colour.orange())
    embed.add_field(name = 'Processing', value='Processing cards, this can take a while...', inline= False)
    msg = await message.send(embed=embed)
    worth=0
    for i in dupes:
        worth+=int(await tcg.getCardPrice(i["id"]))
    await msg.edit(content="Found "+str(len(dupes))+" Cards, do you want to sell them for "+str(worth)+" Pokecoins?",embed=None)
    msgSure = msg
    await msgSure.add_reaction("☑️")
    await msgSure.add_reaction("❌")
    def checkRecSure(emoji,user):
        return user == author and emoji.message.id == msgSure.id
    try:
        reaction, user = await client.wait_for("reaction_add",check=checkRecSure,timeout= 50)
        if(reaction.emoji=="☑️" and user!=client.user):
            for i in dupes:
                collection.remove(i)
            await achievements.addToStats(author,userId,"cardsold",len(dupes))
            editData(userId,Rows.COLLECTION,json.dumps(collection))
            addToData(userId,Rows.BALANCE,worth)
            xp = getData(userId,Rows.XP)
            xpAdded = round(worth/15)
            editData(userId,Rows.XP,xp+xpAdded)
            await achievements.checkForXp(author,userId, xp+xpAdded,xp)
            checkNameMigrated(user.id,user)
            insertHistory(HistoryID.SELLMASS,userId,json.dumps(dupes))
            await msg.edit(content="Succesfully sold!")
            time.sleep(5)
            0/0#Create Exception
        elif(reaction.emoji=="❌" and user!=client.user):
            await msgSure.delete()
    except Exception as e:
        await msgSure.delete()
async def transferMoney(message,authorid):
    try:
        id=message.content
        args=parseArgs(id)
        id=args[1].replace("@","").replace(">","").replace("<","").replace("!","")
        amount=int(args[2])
        if(amount>0):
            if(int(getData(authorid.id,Rows.BALANCE))>=amount):
                addToData(str(authorid.id),Rows.BALANCE,-1*amount)
                addToData(id,Rows.BALANCE,amount)
                await message.channel.send("Succesfully send money")
        else:
            await message.channel.send("Nice try!")
    except:
        await message.channel.send("Invalid request, user 'transfer [@ping at user you whant to transfer PokeCoins to] [amount]'")
async def showCard(message):
    id = parseArgs(message.content)[1]
    embed =  discord.Embed(colour = discord.Colour.orange())
    embed.set_image(url=cardsSingle[id]["imageUrlHiRes"])
    await message.channel.send(embed=embed)

async def help(ctx,author):
    embed = discord.Embed(colour= discord.Colour.orange())
    embed.set_author(name = 'Help')
    embed.add_field(name = '-bal', value='Shows your balance of pokecoins', inline= False)
    embed.add_field(name = '-packs', value='Shows you every booster pack available', inline= False)
    embed.add_field(name = '-collection', value='Sends a link to a website where you can see your collection', inline= False)
    embed.add_field(name = '-buy', value='Allows you to buy packs. Usage: -buy [Pack Name] [add skip to skip the confirmation]', inline= False)
    embed.add_field(name = '-sellduplicates', value='Allows you to sell all duplicates you own', inline= False)
    embed.add_field(name = '-changelog', value='Shows you the changelog', inline= False)
    embed.add_field(name = '-marketplace', value='Sends you a link to the marketplace', inline= False)
    embed.add_field(name = '-vote', value='Get Pokecoins for voting', inline= False)
    embed.add_field(name = '-transfer', value='Transfers PokeCoins to another user. Usage: -transfer [ping at the person PokeCoins should be transfered to] [Amount]', inline= False)
    embed.add_field(name = '-bugreport', value='Send you a link to report a bug', inline= False)
    embed.add_field(name = '-suggestion', value='Send you a link to send Feedback to me', inline= False)
    embed.add_field(name = '-level', value='Shows your xp you have', inline= False)
    embed.add_field(name = '-leaderboard', value='Shows the current leaderboard', inline= False)
    embed.add_field(name = '-profile', value='Shows off you Profile', inline= False)
    embed.add_field(name = '-claim', value='Claim 500 Pokecoins once every 24 Hours', inline= False)
    embed.add_field(name = '-unlockpack', value="Allows you to unlock a new pack", inline=False)
    embed.add_field(name = '-setcompletion', value='Allows to check completion of a set. Usage: -setcompletion [packName]', inline= False)
    embed.add_field(name = '-colour/color', value='Allows you to choose a Profile Colour', inline= False)
    embed.add_field(name = '-show', value='Allows you to show a card. Usage: show [card_id]', inline= False)
    embed.add_field(name = '-support', value='Allows you to buy gems with real money', inline= False)
    embed.add_field(name = '-shop', value='Allows you to buy gems with real money', inline= False)
    embed.add_field(name = '-invite', value='Send an invite for this bot', inline= False)
    await ctx.send( embed=embed)

async def info(ctx):
    embed = discord.Embed(colour= discord.Colour.orange())
    embed.set_author(name = 'Info')
    embed.add_field(name = 'Creator', value="Joshi234#0203", inline= False)
    embed.add_field(name = 'Version', value=str(version), inline= False)
    embed.add_field(name = 'Website', value="https://joshi234.github.io/", inline= False)
    await ctx.send( embed=embed)
async def report(ctx):
    await ctx.send("Send your Bugreports and Suggestions here: https://docs.google.com/forms/d/e/1FAIpQLSdYv0F69h1Zql5cNwqDl0Nw6oFz5dVlGQrHyBr1TUkqml9erQ/viewform?usp=sf_link")

async def changelog(channel):
    embed = discord.Embed(colour= discord.Colour.orange())
    embed.set_author(name = 'Changelog')
    embed.add_field(name = version, value=changelogText, inline= False)
    await channel.send( embed=embed)

async def marketplace(channel):

    await channel.send("Go to the marketplace here: https://joshi234.github.io/marketplace.html")
async def profile(message,author,otherUser=None):
    if(otherUser==None):
        id=author.id
        embed = discord.Embed(colour=int(getData(author.id,Rows.PROFILECOLOUR)))
        embed.set_author(name=author,url="https://joshi234.github.io/",icon_url=author.avatar_url)
    else:
        id=otherUser.id
        embed = discord.Embed()
        embed.set_author(name=otherUser,url="otherUser.avatar_url",icon_url=otherUser.avatar_url)
    badgesLoad = json.loads(getData(id,Rows.BADGE))
    embed.add_field(name="XP",value=str(getData(id,Rows.XP)))
    embed.add_field(name="Pokecoins",value=str(getData(id,Rows.BALANCE))+" Pokecoins")
    embed.add_field(name="Gems",value=str(getData(id,Rows.GEMS))+" Gems")
    embed.add_field(name="Cards Collected",value=str(getCardsCollected(id)))
    data=achievements.loadAchievement(id)
    embed.add_field(name="Packs opened",value=str(data["packsopened"])+" Packs")
    embed.add_field(name="Cards sold",value=str(data["cardsold"])+" Cards")
    if badgesLoad != []:
        string=""
        for i in badgesLoad:
            string+=i+" "
        embed.add_field(name="Badges:",value=string)
    await message.send(embed=embed)

async def showPacks(message,id):
    embed = discord.Embed(colour= discord.Colour.orange())
    embed.set_author(name="Your unlocked packs:")
    length=0
    text=""
    packs=getSpecialItem(id,"packs")
    for i in packs:
        name=i
        length+=len(name)
        if(length>512):
            embed.add_field(name = '\u200b', value=text)
            length=0
            text=name+" \n "
        else:
            text+=name+"\n "
    embed.add_field(name = '\u200b', value=text)
    await message.send("You can unlock more Packs by using -unlockpack or completing Packs. You can check your completion of a set using -setcompletion [pack name]", embed=embed)

async def getServerCount(message):
    await message.channel.send("This bot is on "+str(len(client.guilds))+" Servers")

async def colours(ctx,author):
    colourdict = {"green":3066993,"red":15158332,"blue":3447003,"default":0}
    embed = discord.Embed(colour= discord.Colour.orange())
    availableColours = json.loads(getData(author.id,Rows.SPECIALITEMS))["profileColours"]
    colourString = ""
    for i in availableColours:
        colourString+=i+", "
    embed.add_field(name = "Your available Colours", value=colourString[:len(colourString)-2])
    await ctx.send("Enter your desired profile Colour under this message:",embed=embed)
    def checkd(msg):
        return msg.author == author
    msg = await client.wait_for("message",check=checkd, timeout=25)#allows user 25 seconds to respond
    if(msg.content.lower() in availableColours):
        await ctx.send("Succesfully changed your profile Colour to " + msg.content)
        editData(author.id,Rows.PROFILECOLOUR,colourdict[msg.content.lower()])
    else:
        await ctx.send("Unknown Colour "+msg.content)
async def claim(message,id):
    if(id in claims):
        difference=datetime.datetime.utcnow()-claims[id]
        if(difference.days==0):
            await message.send("500 Pokecoins already claimed for today, you have to wait another "+str(24-round(difference.seconds/3600))+" Hours before you can claim again")
            return

    addToData(id,Rows.BALANCE,500)
    claims[id]=datetime.datetime.utcnow()
    await message.send("500 Pokecoins got added to your balance!")

async def unlockPack(ctx,authorId,author):

    embed = discord.Embed(colour= discord.Colour.orange())
    embed.set_author(name="Available packs")
    embed.add_field(name = 'Enter Random to get a Random Pack for 50 Gems or enter a specific Pack Name to buy it for 100 Gems',value="You can buy Gems here: https://joshi234.github.io/stripe/checkout.html?id="+str(author.id)+ " !This link is only for the one who run the command, generate your own Link if you want to buy gems. You can also get more gems by completing packs",inline=False)
    length=0
    text=""
    packs=list(set(names) - set(getSpecialItem(authorId,"packs")))
    for i in packs:
        name=i
        length+=len(name)
        if(length>512):
            embed.add_field(name = '\u200b', value=text)
            length=0
            text=name+" \n "
        else:
            text+=name+"\n "
    embed.add_field(name = '\u200b', value=text)
    for i in range(len(packs)):
        packs[i] = packs[i].lower()
    msg = await ctx.send( embed=embed)
    def checkd(msg):
        return msg.author == author
    msge = await client.wait_for("message",check=checkd, timeout=30)
    try:
        gems = getData(authorId,Rows.GEMS)
        if(msge.content.lower() == "random"):
            if(gems>=50):
                addToData(authorId,Rows.GEMS,-50)
                pack=getRandomPack(authorId)
                addSpecialItem(authorId,"packs",pack)
                await ctx.send("Succesfully bought: "+str(pack))
                await msg.delete()
            else:
                await msg.delete()
                await ctx.send("Not enough Gems!")
        else:
            if(msge.content.lower() in packs):
                if(gems>=100):
                    addToData(authorId,Rows.GEMS,-100)
                    await msg.delete()
                    addSpecialItem(authorId,"packs",msge.content.title())
                    await ctx.send("Succesfully bought: "+str(msge.content.title()))
                else:
                    await msg.delete()
                    await ctx.send("Not enough Gems!")
    except:
        await msg.delete()
async def vote(ctx):
    await ctx.send("Vote here to get additional 1000 Pokecoins: https://top.gg/bot/806943204830216243/vote")

async def setCompletion(message, author, authorId, ctx):
    pack = message.content.replace(prefix+"setcompletion ","")
    completion,missingCards = await checkIfSetCompleted(author,authorId,pack)
    missing = ""
    embed= discord.Embed(colour = int(getData(author.id,Rows.PROFILECOLOUR)))
    embed.add_field(name = "Completion of the Set "+pack,value=str(round(completion,2))+"%",inline=False)
    if(len(missingCards)!=0):
        if(len(missingCards)<=10):
            for i in missingCards:
                missing += i+"\n"
            embed.add_field(name="Missing Cards", value = missing,inline=False)    
        else:
            embed.add_field(name="Missing Cards", value=str(len(missingCards))+" Missing Cards")
    await ctx.send(embed=embed)
@client.event
async def on_message(message):
    global last_seen
    await client.process_commands(message)
    #print(message.content)
    message.content = message.content.lower()
    if message.author == client.user:
        return
    if(message.content==prefix+"ping"):
        await ping(message.channel)
    if(message.content==prefix+"changelog"):
        await changelog(message.channel)
    if(message.content==prefix+"marketplace"):
        await marketplace(message.channel)
    elif(prefix+"bal" in message.content):
        await bal(message.channel,message.author.id,message.content)
    elif(message.content==prefix+"help"):
        await help(message.channel,message.author)
    elif(message.content==prefix+"packs"):
        await showPacks(message.channel,message.author.id)
    elif(message.content==prefix+"vote"):
        await vote(message.channel)
    elif(message.content==prefix+"info"):
        await info(message.channel)
    elif(message.content==prefix+"level"):
        await level(message.channel, message.author.id)
    elif(message.content==prefix+"invite"):
        await message.channel.send("https://discord.com/oauth2/authorize?client_id=806943204830216243&permissions=273472&scope=bot")   
    elif( message.content == prefix+"profile"):
        await profile(message.channel,message.author)
    elif(message.content==prefix+"leaderboard"):
        await leaderBoard(message.channel)
    elif(message.content==prefix+"colour" or message.content==prefix+"color"):
        await colours(message.channel,message.author)
    elif(message.content==prefix+"servercount"):
        await getServerCount(message)
    elif(message.content==prefix+"shop"):
        await message.channel.send("You can buy Gems here: https://joshi234.github.io/stripe/checkout.html?id="+str(message.author.id)+ " !This link is only for the one who run the command, generate your own Link if you want to buy gems. You can share this link with other people so they can gift gems to you. Thanks for your support!")
    elif(message.content==prefix+"support"):
        await message.channel.send("You can buy Gems here: https://joshi234.github.io/stripe/checkout.html?id="+str(message.author.id)+ " !This link is only for the one who run the command, generate your own Link if you want to buy gems. You can share this link with other people so they can gift gems to you. Thanks for your support!")
    elif(prefix+"show" in message.content):
        await showCard(message)
    elif(message.content==prefix+"unlockpack"):
        await unlockPack(message.channel,message.author.id,message.author)
    elif(message.content==prefix+"claim"):
        await claim(message.channel,message.author.id)
    elif(message.content==prefix+"sellduplicates"):
        await sellDuplicates(message.channel,message.author)
    elif(message.content==prefix+"bugreport" or message.content==prefix+"suggestion"):
        await report(message.channel)
    elif(prefix+"transfer" in message.content):
        await transferMoney(message,message.author)
    elif(prefix+"setcompletion" in message.content):
        await setCompletion(message,message.author,message.author.id,message.channel)
    elif(prefix+"minigame" == message.content):
        await message.channel.send("You can play the minigame here: https://joshi234.github.io/game.html , you can play once every 12 hours and you pick 6 cards and if you get any double, you get to keep the special card")
    elif (prefix+"buy" in message.content):
            await buy_packs(message.channel,message.author,content=message.content)
    elif(message.content==prefix+"collection"):
        await getCollection(message.channel,message.author.id)

    else:
        try:
            try:
                if(time.monotonic()-last_seen[str(message.author.id)])>120:    
                    last_seen[str(message.author.id)]=time.monotonic()
                    addToData(str(message.author.id),Rows.BALANCE,10)
            except:
                last_seen[str(message.author.id)]=time.monotonic()
                addToData(str(message.author.id),Rows.BALANCE,10)
        except:
            last_seen[str(message.author.id)]=time.monotonic()
            
            addToData(str(message.author.id),Rows.BALANCE,10)
            checkNameMigrated(message.author.id,message.author)


def saveCollection():
    global id

    open("id.txt","w").write(str(id))


def loadCollection():
    global id
    try:

        id=int(open("id.txt","r").read())

    except Exception as e:
        traceback.print_exc()
        open("id.txt","x").write(str(0))
        id=0

@slash.slash(name="bal")
async def slashCommand(ctx: SlashContext,args=None):

    if(args!=None):
        message="a "+str(args.id)
        await bal(ctx,ctx.author.id,message,str(args))
    else:
        await bal(ctx,ctx.author.id,"")

@slash.slash(name="vote")
async def slashCommand(ctx: SlashContext,args=None):
    await vote(ctx)

@slash.slash(name="packs")
async def slashCommand(ctx: SlashContext,args=None):
    await showPacks(ctx, ctx.author.id)

@slash.slash(name="collection")
async def slashCommand(ctx: SlashContext,args=None):
    await getCollection(ctx, ctx.author.id)

@slash.slash(name="buy")
async def slashCommand(ctx: SlashContext,name=None,skip=False):
    await buy_packs(ctx,ctx.author,skip,name)

@slash.slash(name="sellduplicates")
async def slashCommand(ctx: SlashContext):
    await sellDuplicates(ctx,ctx.author)

@slash.slash(name="changelog")
async def slashCommand(ctx: SlashContext):
    await changelog(ctx)

@slash.slash(name="marketplace")
async def slashCommand(ctx: SlashContext):
    await marketplace(ctx)

@slash.slash(name="transfer")
async def slashCommand(ctx: SlashContext,user=None,amount=None):
    id=user.id
    if(amount>0):
        if(int(getData(ctx.author.id,Rows.BALANCE))>=amount):
            addToData(str(ctx.author.id),Rows.BALANCE,-1*amount)
            addToData(id,Rows.BALANCE,amount)
            await ctx.send("Succesfully send money")
    else:
        await ctx.send("Nice try!")
        await ctx.send("Send your Bugreports and Suggestions here: https://docs.google.com/forms/d/e/1FAIpQLSdYv0F69h1Zql5cNwqDl0Nw6oFz5dVlGQrHyBr1TUkqml9erQ/viewform?usp=sf_link")

@slash.slash(name="bugreport")
async def slashCommand(ctx: SlashContext):
    await ctx.send("Send your Bugreports and Suggestions here: https://docs.google.com/forms/d/e/1FAIpQLSdYv0F69h1Zql5cNwqDl0Nw6oFz5dVlGQrHyBr1TUkqml9erQ/viewform?usp=sf_link")

@slash.slash(name="suggestion")
async def slashCommand(ctx: SlashContext):
    await ctx.send("Send your Bugreports and Suggestions here: https://docs.google.com/forms/d/e/1FAIpQLSdYv0F69h1Zql5cNwqDl0Nw6oFz5dVlGQrHyBr1TUkqml9erQ/viewform?usp=sf_link")

@slash.slash(name="level")
async def slashCommand(ctx: SlashContext, user=None):
    await level(ctx,ctx.author.id,user)

@slash.slash(name="leaderboard")
async def slashCommand(ctx: SlashContext):
    await leaderBoard(ctx)

@slash.slash(name="profile")
async def slashCommand(ctx: SlashContext, user=None):
    await profile(ctx,ctx.author,user)

@slash.slash(name="claim")
async def slashCommand(ctx: SlashContext):
    await claim(ctx,ctx.author.id)

@slash.slash(name="info")
async def slashCommand(ctx: SlashContext):
    await info(ctx)

@slash.slash(name="colour")
async def slashCommand(ctx: SlashContext):
    await colours(ctx,ctx.author)

@slash.slash(name="color")
async def slashCommand(ctx: SlashContext):
    await colours(ctx,ctx.author)

loadCollection()
#grab command

client.run(config.config["discord_token"])
