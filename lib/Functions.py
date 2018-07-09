from lib.Database import Database
from lib.Config import Config
from lib.ESI import ESI
from flask import session, request, url_for
from requests import get

import time
import json
import math

class Functions:
	def __init__(self):
		self.db = Database()
		self.esi = ESI()
		self.config = Config()
		#self.admins = self.config.getConfig()["settings"]["admins"]
		self.lastUpdate = 0
		self.isRefreshing = False
		self.corpCache = 0
		self.corpAssets = []
		self.itemTranslations = {}
		self.divisions = []
		self.assetNames = {}
		self.officeFlags = {}
		self.priceUpdateCache = 0
		self.bpCache = 0
		self.bps = {}
		self.industryJobs = []
		self.translations = set()
		self.itemTranslations = {}
		self.prices = {}
		self.production = {}
		self.structures = {}
		self.contracts = {}
		self.miningInfo = {}
		self.toProduce = {}
		self.accepted_groups = [
			12 # cargo containers
		]

	def isLoggedIn(self):
		if "token" in session:
			self.db.query("UPDATE users SET ip=%s, lastActive = NOW(), refreshToken = %s WHERE charID = %s",[request.remote_addr,session["token"]["refresh_token"],session["char"]["CharacterID"]])
		return "token" in session

	def getAuthURI(self):
		return self.esi.getAuthURI()

	def checkInUser(self, code):
		if "token" in session:
		#if session["token"]:
			#Trying to add to current user!!
			tokens = self.esi.getToken(code)
			verifyChar = self.esi.getESIChar(tokens)
			if verifyChar["CharacterID"] == session["char"]["CharacterID"]:
				#Cant add yourself..
				return False
			cur = self.db.query("SELECT COUNT(*) FROM subchars WHERE charID = %s",[verifyChar["CharacterID"]])
			if cur.fetchone()[0] > 0:
				#Already added
				return False

			cur = self.db.query("""
								INSERT INTO subchars (`charName`,`charID`,`mainID`,`accessToken`,`refreshToken`)
								VALUES (%s,%s,%s,%s,%s)
				""",[
					verifyChar["CharacterName"],
					verifyChar["CharacterID"],
					session["char"]["CharacterID"],
					tokens["access_token"],
					tokens["refresh_token"]
				])


			#Reset security object to logged in user..
			curchar = self.esi.getESIChar(session["token"])
			return False
		else:
			session["token"] = self.esi.getToken(code)
			r = self.esi.isVerified(session["token"])
			cur = self.db.query("SELECT COUNT(*) FROM users WHERE charID = %s",[session["char"]["CharacterID"]])
			if cur.fetchone()[0] == 0:
				cur = self.db.query("""
										INSERT INTO users
											(`charID`, `charName`, `ip`, `groupName`)
										VALUES
											(%s, %s, %s, %s)	
				""",[session["char"]["CharacterID"], session["char"]["CharacterName"], request.remote_addr, "Unknowns"])

			return r

	def isVerified(self):
		if not "token" in session:
			return False
		session["isAdmin"] = False
		session["isMember"] = False
		if "char" in session:
			self.db.query("UPDATE users SET ip=%s, lastActive = NOW(), refreshToken = %s WHERE charID = %s",[request.remote_addr,session["token"]["refresh_token"],session["char"]["CharacterID"]])
			try:
				session["corpID"] = self.getCorpID()
				cur = self.db.query("SELECT groupName FROM users WHERE charID = %s",[session["char"]["CharacterID"]])
				grName = cur.fetchone()[0]
				if grName == "Leaders":
					session["isAdmin"] = True
					session["isMember"] = True
				if grName == "Members":
					session["isMember"] = True
				#if session["char"]["CharacterID"] in self.admins:
				#	session["isAdmin"] = True
			except:
				return False
		return self.esi.isVerified(session["token"])

	def logoutUser(self):
		session.pop('token',None)
		session.pop('char', None)

	def isAdmin(self):
		return session["isAdmin"]

	def isMember(self):
		return session["isMember"]

	def getCharacters(self):
		users = []
		cur = self.db.query("SELECT charID, charName, groupName, UNIX_TIMESTAMP(lastActive) FROM users")
		for r in cur.fetchall():
			charID,charName,groupName,lastActive = r
			users.append({
				"charID": charID,
				"charName": charName,
				"groupName": groupName,
				"lastActive": int(lastActive)*1000
			})
		return users

	def editCharacter(self, form):
		charID = form["charID"]
		group = form["group"]

		if charID is not None and group is not None:
			self.db.query("UPDATE users SET groupName = %s WHERE charID = %s",[group,charID])
	
		return {}

	def getCharID(self):
		char = self.esi.getESIChar(session["token"])
		return char['CharacterID']

	def getCorpID(self):
		charID = self.getCharID()
		corpID = self.esi.getESIInfo('get_characters_character_id', {"character_id": charID})
		return corpID["corporation_id"]

	def getCharSysLocID(self):
		charID = self.getCharID()
		charLocID = self.esi.getESIInfo('get_characters_character_id_location', {"character_id": charID})
		return charLocID["solar_system_id"]

	def getUserInfo(self):
		charID = self.getCharID()

		charLocID = self.getCharSysLocID()
		charLoc = self.esi.getESIInfo('get_universe_systems_system_id', {"system_id": charLocID})
		session["curLoc"] = charLoc['name']

	def getWalletInfo(self):
		charID = self.getCharID()
		itemList = set()

		wallet = self.esi.getESIInfo('get_characters_character_id_wallet', {"character_id": charID})

		walletTrans = self.esi.getESIInfo('get_characters_character_id_wallet_transactions', {"character_id": charID})
		transactions = []
		citadels = set()
		for t in walletTrans:
			t["date"] = int(time.mktime(time.strptime(str(t["date"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			itemList.add(t["type_id"])
			if t["location_id"] <= 69999999:
				itemList.add(t["location_id"])
			else:
				citadels.add(t["location_id"])
			transactions.append(t)
			if t["is_buy"]:
				amount = t["unit_price"] * t["quantity"] * -1
			else:
				amount = t["unit_price"] * t["quantity"]
			cur = self.db.query("""
								INSERT IGNORE INTO wallet 
									(`ref_id`,`charID`,`date`,`is_transaction`,`in_out`) 
								VALUES 
									(%s,%s,%s,%s,%s)
								""",[t["transaction_id"],charID,t["date"],True,amount])

		walletJourn = self.esi.getESIInfo('get_characters_character_id_wallet_journal', {"character_id": charID})
		journal = []
		factions = []
		for j in walletJourn:
			j["date"] = int(time.mktime(time.strptime(str(j["date"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			journal.append(j)
			if "first_party_id" in j:
				if j["first_party_id"] > 500000 and j["first_party_id"] < 600000:
					factions.append(j["first_party_id"])
				else:
					itemList.add(j["first_party_id"])
			if "second_party_id" in j:
				itemList.add(j["second_party_id"])

			cur = self.db.query("""
								INSERT IGNORE INTO wallet 
									(`ref_id`,`charID`,`date`,`is_transaction`,`balance`,`in_out`) 
								VALUES 
									(%s,%s,%s,%s,%s,%s)
								""",[j["id"],charID,j["date"],False,j["balance"],j["amount"]])

		itemTranslation = {}
		if len(itemList)>0:
			itemTranslations = self.esi.getESIInfo('post_universe_names', {"ids": itemList})
			for i in itemTranslations:
				itemTranslation[i['id']] = i["name"]
			factionlist = self.esi.getESIInfo('get_universe_factions',{})
			for f in factionlist:
				if f["faction_id"] in factions:
					itemTranslation[f["faction_id"]] = f["name"]
		if len(citadels)>0:
			for s in citadels:
				citadelInfo = self.esi.getESIInfo('get_universe_structures_structure_id',{"structure_id":s})
				itemTranslation[s] = citadelInfo["name"]

		cur = self.db.query("SELECT `date`,is_transaction,balance FROM wallet WHERE charID = %s ORDER BY `date` ASC",[charID])
		walletHistory = []
		for w in cur.fetchall():
			datestamp,is_transaction,balance = w

			if is_transaction:
				continue

			walletHistory.append({
				"datestamp": datestamp,
				"balance": balance
			})
		return {"wallet": wallet, "transactions": transactions, "journal": journal, "itemTranslation": itemTranslation, "walletHistory": walletHistory}

	def getMarketInfo(self):
		charID = self.getCharID()
		itemList = set()

		marketOpen = self.esi.getESIInfo('get_characters_character_id_orders', {"character_id": charID})
		openorders = []
		for o in marketOpen:
			o["issued"] = int(time.mktime(time.strptime(str(o["issued"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			openorders.append(o)
			itemList.add(o["region_id"])
			itemList.add(o["type_id"])
			itemList.add(o["location_id"])

		marketHist = self.esi.getESIInfo('get_characters_character_id_orders_history', {"character_id": charID})
		history = []
		for h in marketHist:
			if "issued" in h:
				h["issued"] = int(time.mktime(time.strptime(str(h["issued"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			history.append(h)
		itemTranslation = {}
		if len(itemList)>0:
			itemTranslations = self.esi.getESIInfo('post_universe_names', {"ids": itemList})
			for i in itemTranslations:
				itemTranslation[i['id']] = i["name"]

		return {"open": openorders, "history": history, "itemTranslation": itemTranslation}

	def getIndustryJobs(self):
		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["jobs"])
		r = cur.fetchone()
		if r:
			jobs = r[0]
		else:
			jobs = []

		with open('tempstore/bps.json') as f:
			bps = json.load(f)

		with open('tempstore/translations.json') as f:
			trans = json.load(f)
		return {"jobs": json.loads(jobs), "translations": trans, "bps": bps}

	def getCorpAssets(self):
		with open('tempstore/assets.json') as f:
			assets = json.load(f)

		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["divisions"])
		r = cur.fetchone()
		if r:
			divisions = r[0]
		else:
			divisions = []

		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["flags"])
		r = cur.fetchone()
		if r:
			flags = r[0]
		else:
			flags = []

		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["assetnames"])
		r = cur.fetchone()
		if r:
			assetsnames = r[0]
		else:
			assetsnames = []

		with open('tempstore/translations.json') as f:
			trans = json.load(f)
		return {
			"assets": assets, 
			"translations": trans, 
			"divisions": json.loads(divisions), 
			"assetnamelist": json.loads(assetsnames), 
			"officeFlags": json.loads(flags)
		}

	def getMarketItems(self):
		results = []
		if "q" in request.args:
			cur = self.db.query("SELECT invTypes.typeID, typeName FROM invTypes LEFT JOIN priceLookup P ON P.typeID = invTypes.typeID WHERE marketGroupID IS NOT NULL AND typeName LIKE %s AND P.typeID IS NULL AND typeName NOT LIKE %s",["%"+request.args["q"]+"%","%blueprint%"])
			for r in cur.fetchall():
				results.append({"id": r[0], "text": r[1]})
		return {"results": results}

	def postMarketItems(self):
		items = request.form.getlist("items[]")
		for item in items:
			self.db.query("INSERT INTO priceLookup (typeID, iskBuy, iskSell) VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE iskBuy = iskBuy, iskSell=iskSell",[item,"0","0"])
		return {}

	def getPricingInfo(self):
		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["prices"])
		r = cur.fetchone()
		if r:
			items = r[0]
		else:
			items = {}

		with open('tempstore/translations.json') as f:
			trans = json.load(f)
		return {"items": json.loads(items), "translations": trans}

	def delMarketItem(self, itemID):
		self.db.query("DELETE FROM priceLookup WHERE typeID = %s",[itemID])
		return {}

	def getContracts(self):
		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["contracts"])
		r = cur.fetchone()
		if r:
			contracts = r[0]
		else:
			contracts = {}

		with open('tempstore/translations.json') as f:
			trans = json.load(f)
		return {"contracts": json.loads(contracts), "translations": trans}
	
	def getMoonMining(self):
		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["moon"])
		r = cur.fetchone()
		if r:
			mining = r[0]
		else:
			mining = {}

		with open('tempstore/translations.json') as f:
			trans = json.load(f)
		return {"mining": json.loads(mining), "translations": trans}

	def getProduction(self):
		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["production"])
		r = cur.fetchone()
		if r:
			prod = r[0]
		else:
			prod = {}

		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["toproduce"])
		r = cur.fetchone()
		if r:
			toproduce = r[0]
		else:
			toproduce = {}

		with open('tempstore/translations.json') as f:
			trans = json.load(f)
		return {"production": json.loads(prod), "translations": trans, "toProduce": json.loads(toproduce)}

	def getStructures(self):
		cur = self.db.query("SELECT json FROM autoupdate WHERE type = %s",["structures"])
		r = cur.fetchone()
		if r:
			return {"structures": json.loads(r[0])}
		else:
			return {"structures": {}}
	
	def setTarget(self, selID, val):
		self.db.query("UPDATE priceLookup SET toBuild = %s WHERE typeID = %s",[val, selID])
		for p in self.toProduce:
			try:
				if "dbid" in self.toProduce[p]:
					if self.toProduce[p]["dbid"] == int(selID):
						self.toProduce[p]["quantity"] = val
			except:
				continue
		return
	
	def getRefreshingStatus(self):
		return {"isRefreshing": self.isRefreshing, "time": self.lastUpdate}