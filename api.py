from sqlite3.dbapi2 import Row
import flask
import json
from flask import jsonify,request
from flask_cors import CORS
import requests,os
from database import *
import tcgplayer as tcg
import string
import random
from datetime import datetime, timedelta
import stripe
import asyncio
stripe.api_key = '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'
app = flask.Flask(__name__)

CORS(app)
app.config["DEBUG"] = True
#app.config["ssl_context"]=(r"C:\Users\Joshua\server.crt",r"C:\Users\Joshua\server.key")
marketplace=[]
counts={}
gamecache = {}
gameids = {"dev":"455370586630258688"}
def getApp():
    start_response("200 OK", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(data)))
    ])
    return iter([data])
@app.route('/', methods=['GET'])
def home():
    return "Welcome!"

@app.route('/api/v1/collection', methods=['GET'])
def getCollection():

    if "id" in request.args:
        
        return getData(request.args["id"],Rows.COLLECTION)
    elif "access_token" in request.args:
        r=json.loads(getId(request.args["access_token"]))["id"]
        return getData(r,Rows.COLLECTION)
    else:
        return "Invalid Request"
@app.route('/api/v1/marketplace', methods=['GET'])
def getMarketplace():
    global marketplace
    return jsonify(marketplace)
@app.route('/api/v1/sell', methods=['GET'])
def sellCard():
    global marketplace
    card_id=request.args["card_id"]
    acces_token=request.args["access_token"]
    price=request.args["price"]
    id=json.loads(getId(acces_token))["id"]
    collection=json.loads(getData(id,Rows.COLLECTION))
    for i in collection:

            if(str(i["card_id"])==str(card_id)):

                collection.remove(i)
                editData(id,Rows.COLLECTION,json.dumps(collection))
                i["price"]=str(price)
                i["owner"]=str(id)
                
                marketplace.append(i)
                saveMarketplace()
                return "Put in marketplace!"
    return "You don't own this card"
@app.route('/api/v1/issue', methods=['GET'])
def getIssud():
    return str(getIssued(str(request.args["card_id"])))

@app.route('/api/v1/profile/pic', methods=['GET'])
def getProfilePic():
    requestId=json.loads(getId(request.args["access_token"]))
    
    return "https://cdn.discordapp.com/avatars/"+requestId["id"]+"/"+requestId["avatar"]
@app.route('/api/v1/balance', methods=['GET'])
def getBal():
    id=json.loads(getId(request.args["access_token"]))["id"]
    return str(getData(id,Rows.BALANCE))
@app.route('/api/v1/vote', methods=['POST'])
def vote():
    args=json.loads(request.data)
    addToData(args["user"],Rows.BALANCE,1000)
    insertHistory
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    
@app.route('/api/v1/profile/valid', methods=['GET'])
def getProfileValid():
    requestId=json.loads(getId(request.args["access_token"]))
    if("id" in requestId):
        return "1"
    else:
        return "0"
loop = asyncio.get_event_loop()

@app.route('/api/v1/cards/price', methods=['GET'])
def getCardPrice():
    try:
        id=request.args["id"]
        price = tcg.getCardPriceBlocking(id)
        return str(price)
    except Exception as e:
        return "Invalid Card id"
        
@app.route('/api/v1/collection/collected', methods=['GET'])
def getCollectedCard():
    id=json.loads(getId(request.args["access_token"]))["id"]
    return str(getCardsCollected(id))

@app.route('/api/v1/sell/bot', methods=['GET'])
def sellCardToBot():
    card_id=request.args["id"]
    acces_token=request.args["access_token"]
    
    id=json.loads(getId(acces_token))["id"]
    collection=json.loads(getData(id,Rows.COLLECTION))
    for i in collection:
            if(str(i["card_id"])==str(card_id)):
                price= tcg.getCardPriceBlocking(i["id"])
                collection.remove(i)
                editData(id,Rows.COLLECTION,json.dumps(collection))
                addToData(id,Rows.BALANCE,price)
                #addToData(id,Rows.XP,round(price/10))
                return "Sold"
    return "You don't own this card"

@app.route('/api/v1/games/getid', methods=['GET'])
def getGameId():
    acces_token=request.args["access_token"]
    id=json.loads(getId(acces_token))["id"]
    if(id in gamecache):
        difference : timedelta 
        difference=datetime.utcnow()-gamecache[id]
        if(difference.seconds<43200):
            return str("0")
        else:
            gamecache[id] = datetime.utcnow()
            rand = get_random_string(32)
            gameids[rand] = id
            return str(rand)
    else:
        gamecache[id] = datetime.utcnow()
        rand = get_random_string(32)
        gameids[rand] = id
        return str(rand)

@app.route('/api/v1/games/uploaddata', methods=['POST'])
def uploadGameData():
    gameId=request.args["id"]
    cards = json.loads(request.args["data"])["cards"]
    if(gameId in gameids):
        userId = gameids[gameId]
        collection = json.loads(getData(userId,Rows.COLLECTION))
        for i in cards:
            card = {
                'id':'special-'+str(i),
                'imageUrl' : 'https://joshi234.github.io/special/'+str(i)+".png",
                'imageUrlHiRes' : 'https://joshi234.github.io/special/'+str(i)+".png",
                'card_id' : gameId,
                'rarity' : 'special',
                'set' : 'Special Cards',
                'setCode' : 'special',
                'issue' : getIssued('special-'+str(i))
            }
            collection.append(card)
            addIssued('special-'+str(i))
        editData(userId, Rows.COLLECTION, json.dumps(collection))
        del gameids[gameId]
        return "0"
    return "1"
@app.route('/api/v1/buy', methods=['GET'])
def buyCard():
    global marketplace

    card_id=request.args["card_id"]
    acces_token=request.args["access_token"]
    id=json.loads(getId(acces_token))["id"]
    
    for i in marketplace:
        #print(i["card_id"])
        if(str(i["card_id"])==str(card_id)):
           
            price=i["price"]
            owner=i["owner"]
            if(int(getData(id,Rows.BALANCE))-int(price) < 0):
                return "Not Enough Money"
            marketplace.remove(i)
            del i["price"]
            del i["owner"]
            collection=json.loads(getData(id,Rows.COLLECTION))
            collection.append(i)
            
            saveMarketplace()
            addToData(id,Rows.BALANCE,-1*int(price))
            addToData(owner,Rows.BALANCE,price)
            editData(id,Rows.COLLECTION,json.dumps(collection))
            return "Succes"
    return "Error"
def getId(access_token):
    return requests.get("https://discordapp.com/api/users/@me", headers={"Authorization":"Bearer "+access_token}).content


def saveMarketplace():
    global marketplace
    open("marketplace.json","w").write(json.dumps(marketplace))
def loadMarketplace():
    global marketplace
    if(os.path.exists("marketplace.json")):
        marketplace=json.loads(open("marketplace.json","r").read())

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

YOUR_DOMAIN = 'https://joshi234.github.io/stripe/'

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        id = request.args["id"]
        if(id=="null"):
            return jsonify(error="invalid id"), 403
        if(request.args["region"]=="eu"):
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card','bancontact','giropay','sofort'],
                line_items=[
                    {
                        'price' : "price_1IjncLEtNol6v51apbVN13Hx",
                        'quantity': request.args["amount"],
                    },
                ],            
                metadata={"id":request.args['id']},

                mode='payment',
                success_url=YOUR_DOMAIN + 'success.html',
                cancel_url=YOUR_DOMAIN + 'cancel.html',
            )
        else:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price' : "price_1IjoczEtNol6v51aNZP9SJe0",
                        'quantity': request.args["amount"],
                    },
                ],
                mode='payment',
                metadata={"id":request.args["id"]},
                success_url=YOUR_DOMAIN + 'success.html',
                cancel_url=YOUR_DOMAIN + 'cancel.html',
            )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        print(e)
        return jsonify(error=str(e)), 403


endpoint_secret = "whsec_fYDK1UK7n8BubzozrASAUyGdorgJEkij"
@app.route("/stripe", methods=['POST'])
def bought():
    payload = request.data
    print(payload.decode('utf-8'))
    sig_header = request.headers['Stripe-Signature']
    event = None

    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        resp = jsonify(success=False)
        resp.status_code=400
        return resp
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        resp = jsonify(success=False)
        resp.status_code=400
        return resp
    event = json.loads(request.data)
    price = int(event["data"]["object"]["amount_total"])
    id = str(event["data"]["object"]["metadata"]["id"])
    print("Price : "+str(price))
    print("Id: "+id)
    addToData(id,Rows.GEMS,price)
  # Passed signature verification
    resp = jsonify(success=True)
    resp.status_code=200
    return resp
loadMarketplace()
#app.run()
