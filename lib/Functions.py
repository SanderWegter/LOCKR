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
		self.admins = self.config.getConfig()["settings"]["admins"]
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
											(`charID`, `charName`, `ip`)
										VALUES
											(%s, %s, %s)	
				""",[session["char"]["CharacterID"], session["char"]["CharacterName"], request.remote_addr])

			return r

	def isVerified(self):
		if not "token" in session:
			return False
		session["isAdmin"] = False
		if "char" in session:
			self.db.query("UPDATE users SET ip=%s, lastActive = NOW(), refreshToken = %s WHERE charID = %s",[request.remote_addr,session["token"]["refresh_token"],session["char"]["CharacterID"]])
			try:
				session["corpID"] = self.getCorpID()
				if session["char"]["CharacterID"] in self.admins:
					session["isAdmin"] = True
			except:
				return False
		return self.esi.isVerified(session["token"])

	def logoutUser(self):
		session.pop('token',None)
		session.pop('char', None)

	def isAdmin(self):
		return session["isAdmin"]

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
		return {"jobs": self.industryJobs, "translations": self.itemTranslations, "bps": self.bps}

	def getCorpAssets(self):
		return {"assets": self.corpAssets, "translations": self.itemTranslations, "divisions": self.divisions, "assetnamelist": self.assetNames, "officeFlags": self.officeFlags}

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
		return {"items": self.prices, "translations": self.itemTranslations}

	def delMarketItem(self, itemID):
		self.db.query("DELETE FROM priceLookup WHERE typeID = %s",[itemID])
		return {}

	def updatePrice(self):
		#TEMP until i figure out calcs myself...
		#JITA_REGION = 10000002
		#JITA SYSTEM = 30000142
		#Avg = (jita[buy][max] + jita[sell][min]) / 2
		baseURL = "https://api.evemarketer.com/ec/marketstat/json?usesystem=30000142&typeid="
		
		if int(time.time() - self.priceUpdateCache) > 3600:
			self.priceUpdateCache = int(time.time())

			cur = self.db.query("SELECT typeID FROM priceLookup")
			items = []
			for t in cur.fetchall():
				items.append(str(t[0]))
			items = ",".join(items)

			r = get(baseURL+items)
			marketInfo = r.json()
			for r in marketInfo:
				print(r)
				typeID = r["buy"]["forQuery"]["types"][0]
				buy = r["buy"]["fivePercent"]
				sell = r["sell"]["fivePercent"]
				cur = self.db.query("UPDATE priceLookup SET iskBuy = %s, iskSell = %s WHERE typeID = %s",[buy,sell,typeID])
		return {}

	def getContracts(self):
		return {"contracts": self.contracts, "translations": self.itemTranslations}
	
	def getMoonMining(self):
		return {"mining": self.miningInfo}

	def getProduction(self):
		return {"production": self.production, "translations": self.itemTranslations, "toProduce": self.toProduce}

	def getStructures(self):
		return {"structures": self.structures}
	
	def updateIndustryJobs(self, corpID):
		print("Industryjobs")
		industry = self.industryJobs
		
		industryJobs = self.esi.getESIInfo('get_corporations_corporation_id_industry_jobs', {"corporation_id": corpID})
		industry = []
		citadels = set()
		for i in industryJobs:
			if "end_date" in i:
				i["end_date"] = int(time.mktime(time.strptime(str(i["end_date"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "start_date" in i:
				i["start_date"] = int(time.mktime(time.strptime(str(i["start_date"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "blueprint_type_id" in i:
				self.translations.add(i["blueprint_type_id"])
			if "installer_id" in i:
				self.translations.add(i["installer_id"])
			
			if i["blueprint_location_id"] < 69999999:
				self.translations.add(i["location_id"])
			else:
				citadels.add(i["location_id"])
			industry.append(i)

		if len(citadels) > 0:
			for s in citadels:
				citadelInfo = self.esi.getESIInfo('get_universe_structures_structure_id',{"structure_id":s})
				if "name" in citadelInfo:
					self.itemTranslations[s] = citadelInfo["name"]
				else:
					self.itemTranslations[s] = "Unknown - No permissions"

		self.industryJobs = industry
		return
	
	def updateBps(self, corpID):
		print("BPS")
		bps = self.bps
		blueprints = self.esi.getESIInfoMP('get_corporations_corporation_id_blueprints',{"corporation_id": corpID})
		for p in blueprints:
			for bp in p[1].data:
				bps[bp["item_id"]] = {
									"location": bp["location_id"],
									"type": bp["quantity"], 
									"type_id": bp["type_id"], 
									"me": bp["material_efficiency"],
									"te": bp["time_efficiency"]
									}
		self.bps = bps

	def updateDivisions(self, corpID):
		print("Divisions")
		divisions = self.divisions
		divisions = self.esi.getESIInfo('get_corporations_corporation_id_divisions',{"corporation_id": corpID})
		self.divisions = divisions

	def updateCorpAssets(self, corpID):
		print("Assets")
		assets = []
		citadels = set()
		officeFlags = self.officeFlags
		assetList = self.esi.getESIInfoMP('get_corporations_corporation_id_assets', {"corporation_id": corpID})
		for a in assetList:
			for asset in a[1].data:
				if asset["location_id"] < 69999999:
					self.translations.add(asset["location_id"])
				else:
					citadels.add(asset["location_id"])
				
				if asset["location_flag"] == "OfficeFolder" or "CorpSAG" in asset["location_flag"]:
					officeFlags[asset["item_id"]] = asset["location_id"]
				if asset["type_id"] < 69999999:
					self.translations.add(asset["type_id"])
				assets.append(asset)

		self.updateOfficeFlags()
		officeFlags = self.officeFlags

		nw = []
		for a in assets:
			group_id = self.esi.getESIInfo('get_universe_types_type_id',{'type_id': a["type_id"]})
			if group_id["group_id"] in self.accepted_groups:
				aName = self.esi.getESIInfo('post_corporations_corporation_id_assets_names',{'corporation_id': corpID, "item_ids": [a['item_id']]})
				try:
					self.assetNames[a["item_id"]] = aName[0]["name"]
					a["itemName"] = aName[0]["name"]
				except:
					pass
			if a["location_id"] in officeFlags:
				a["orig_location_id"] = a["location_id"]
				a["location_id"] = officeFlags[a["location_id"]]
				if a["location_id"] < 69999999:
					self.translations.add(a["location_id"])
				else:
					citadels.add(a["location_id"])
			nw.append(a)
		self.corpAssets = nw
		if len(citadels) > 0:
			for s in citadels:
				citadelInfo = self.esi.getESIInfo('get_universe_structures_structure_id',{"structure_id":s})
				if "name" in citadelInfo:
					self.itemTranslations[s] = citadelInfo["name"]
				else:
					self.itemTranslations[s] = "Unknown - No permissions"
		return

	def updateContracts(self, corpID):
		print("Contracts")
		citadels = set()
		contracts = self.contracts
		contractList = self.esi.getESIInfoMP('get_corporations_corporation_id_contracts', {"corporation_id": corpID})
		for c in contractList:
			for contract in c[1].data:
				contracts[contract["contract_id"]] = contract

		for c in contracts:
			if "date_expired" in contracts[c]:
				contracts[c]["date_expired"] = int(time.mktime(time.strptime(str(contracts[c]["date_expired"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "date_issued" in contracts[c]:
				contracts[c]["date_issued"] = int(time.mktime(time.strptime(str(contracts[c]["date_issued"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "date_completed" in contracts[c]:
				contracts[c]["date_completed"] = int(time.mktime(time.strptime(str(contracts[c]["date_completed"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "date_accepted" in contracts[c]:
				contracts[c]["date_accepted"] = int(time.mktime(time.strptime(str(contracts[c]["date_accepted"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000

			self.translations.add(contracts[c]["acceptor_id"])
			if "end_location_id" in contracts[c]:
				if contracts[c]["end_location_id"] < 69999999:
					self.translations.add(contracts[c]["end_location_id"])
				else:
					citadels.add(contracts[c]["end_location_id"])
			self.translations.add(contracts[c]["issuer_id"])
			self.translations.add(contracts[c]["issuer_corporation_id"])
			if "start_location_id" in contracts[c]:
				if contracts[c]["start_location_id"] < 69999999:
					self.translations.add(contracts[c]["start_location_id"])
				else:
					citadels.add(contracts[c]["start_location_id"])
		
		if len(citadels) > 0:
			for s in citadels:
				citadelInfo = self.esi.getESIInfo('get_universe_structures_structure_id',{"structure_id":s})
				if "name" in citadelInfo:
					self.itemTranslations[s] = citadelInfo["name"]
				else:
					self.itemTranslations[s] = "Unknown - No permissions"

		self.contracts = contracts
		return
	
	def updateMoonMining(self, corpID):
		print("Moonmining")
		miningVar = []
		miningVar = self.esi.getESIInfo("get_corporation_corporation_id_mining_extractions",{"corporation_id": corpID})
		for m in miningVar:
			if "chunk_arrival_time" in m:
				m["chunk_arrival_time"] = int(time.mktime(time.strptime(str(m["chunk_arrival_time"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "extraction_start_time" in m:
				m["extraction_start_time"] = int(time.mktime(time.strptime(str(m["extraction_start_time"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "natural_decay_time" in m:
				m["natural_decay_time"] = int(time.mktime(time.strptime(str(m["natural_decay_time"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
		
		observerVar = self.esi.getESIInfo("get_corporation_corporation_id_mining_observers", {"corporation_id": corpID})
		for o in observerVar:
			if "last_updated" in o:
				o["last_updated"] = int(time.mktime(time.strptime(str(o["last_updated"]),'%Y-%m-%d')))*1000

		self.mining = {"extractions": miningVar, "observers": observerVar}
		return

	def updateTranslations(self):
		print("Translations")
		if len(self.translations)>0:
			cur = self.db.query("SELECT idnum,name,marketGroup FROM itemLookup")
			row = cur.fetchall()
			for r in row:
				try:
					self.translations.remove(r[0])
				except:
					pass
				self.itemTranslations[r[0]] = {'name': r[1], 'group': r[2]}
				
			itemTranslation = self.esi.getESIInfo('post_universe_names', {"ids": self.translations})
			for i in itemTranslation:
				itemTypeLookup = self.esi.getESIInfo('get_universe_types_type_id',{"type_id": i["id"]})
				marketGroupName = ["Unknown"]
				if "market_group_id" in itemTypeLookup:
					marketGroupName = []
					marketGroup = self.esi.getESIInfo('get_markets_groups_market_group_id',{"market_group_id": itemTypeLookup["market_group_id"]})
					while "parent_group_id" in marketGroup:
						marketGroupName.append(marketGroup["name"])
						marketGroup = self.esi.getESIInfo('get_markets_groups_market_group_id',{"market_group_id": marketGroup["parent_group_id"]})
					marketGroupName.reverse()
					marketGroupName = " > ".join(marketGroupName)
					self.itemTranslations[i["id"]] = {"name": i["name"], "group": marketGroupName}
					cur = self.db.query("DELETE FROM itemLookup WHERE idnum = %s",[i["id"]])
					cur = self.db.query("INSERT INTO itemLookup (`idnum`,`name`,`marketGroup`) VALUES (%s,%s,%s)",[i['id'],i['name'],marketGroupName])
				else:
					self.itemTranslations[i["id"]] = {"name": i["name"], "group": marketGroupName}

		return

	def updateOfficeFlags(self):
		print("Officeflags")
		for k in self.officeFlags:
			try:
				self.officeFlags[k] = self.officeFlags[self.officeFlags[k]]
			except:
				pass
		return

	def updatePrices(self):
		tempTrans = set()
		cur = self.db.query("SELECT typeID, iskBuy, iskSell FROM priceLookup")
		for r in cur.fetchall():
			self.translations.add(r[0])
			tempTrans.add(r[0])
			self.prices[r[0]] = {"iskBuy": r[1], "iskSell": r[2], "materials": {}}

		itemTranslations = {}
		itemTranslation = self.esi.getESIInfo('post_universe_names', {"ids": tempTrans})
		for i in itemTranslation:
			itemTranslations[i["id"]] = {"name": i["name"]}

		for p in self.prices:
			bpItemID = self.esi.getESIInfo('get_search',{'strict': 'true', 'search': itemTranslations[p]["name"]+" Blueprint", 'categories': "inventory_type"})
			try:
				bpID = bpItemID["inventory_type"]
				cur = self.db.query("SELECT materialTypeID, quantity FROM industryActivityMaterials WHERE activityID = %s AND typeID = %s",[1,bpID])
				res = cur.fetchall()
				if len(res)>0:
					for m in res:
						self.translations.add(m[0])
						USED_ME = 5
						mats = math.ceil((m[1] * ((99)/100) * ((100-USED_ME)/100)))
						self.prices[p]["materials"].update({m[0]: mats})
			except Exception as e:
				pass
		self.updatePrice()
		return

	def updateProduction(self):
		print("Production")
		cur = self.db.query("SELECT typeID, toBuild FROM priceLookup LEFT JOIN itemLookup I ON I.idnum = typeID WHERE I.name NOT LIKE %s AND marketGroup LIKE %s",["%blueprint%","%Ships >%"])
		
		prods = ()
		tempTrans = set()
		for r in cur.fetchall():
			tempTrans.add(r[0])
			prods = prods + (r[0],)
			self.toProduce[r[0]] = r[1]

		if len(tempTrans) > 0:
			itemTranslations = {}
			itemTranslation = self.esi.getESIInfo('post_universe_names', {"ids": tempTrans})
			for i in itemTranslation:
				print(i)
				itemTranslations[i["id"]] = {"name": i["name"]}

		prodBP = ()
		for p in prods:
			bpItemID = self.esi.getESIInfo('get_search',{'strict': 'true', 'search': itemTranslations[p]["name"]+" Blueprint", 'categories': "inventory_type"})
			prodBP = prodBP + (bpItemID["inventory_type"][0],)
			self.toProduce[bpItemID["inventory_type"][0]] = {'quantity': self.toProduce[p], 'dbid': p}

		format_strings = ','.join(['%s'] * len(prodBP))
		cur = self.db.query("SELECT typeID,materialTypeID, quantity FROM `industryActivityMaterials` WHERE `typeID` IN (%s) AND activityID = 1" % format_strings, prodBP)
		prodMats = {}
		for r in cur.fetchall():
			if r[0] not in prodMats:
				prodMats[r[0]] = {}
			prodMats[r[0]][r[1]] = {"quantity": r[2], "stock": 0, "inbuild": 0}

		assets = self.corpAssets
		for a in assets:
			for p in prodMats:
				for i in prodMats[p]:
					if a["type_id"] == i:
						prodMats[p][i]["stock"] += a["quantity"]
		
		inbuild = self.industryJobs
		for job in inbuild:
			for p in prodMats:
				for i in prodMats[p]:
					if job["product_type_id"] == i:
						prodMats[p][i]["inbuild"] += job["runs"]

		self.production = prodMats
		return
	
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

	def updateStructures(self, corpID):
		print("Structures")
		return
	
	def getRefreshingStatus(self):
		return {"isRefreshing": self.isRefreshing, "time": self.lastUpdate}

	def updateAllData(self):
		print("Starting update")
		print("Checking server status")
		res = get("https://esi.evetech.net/latest/status/")
		try:
			r = res.json()
			print(r)
		except:
			r = {"error": "None"}
		
		if "error" in r or r["players"] == 0:
			print("Server offline.")
			return

		self.isRefreshing = True
		self.translations = set()
		cur = self.db.query("SELECT charID,refreshToken FROM users WHERE LENGTH(refreshToken) > 2")
		for r in cur.fetchall():
			charID,refreshToken = r
			self.esi.subToken(refreshToken)
			self.esi.getForceRefresh()
			roles = self.esi.getESIInfo('get_characters_character_id_roles',{"character_id": charID})
			baseroles = roles["roles"]
			#corpID = self.getCorpID()
			charInfo = self.esi.getESIInfo('get_characters_character_id',{"character_id": charID})
			corpID = charInfo["corporation_id"]
			if "Director" in baseroles:
				self.updateIndustryJobs(corpID)
				self.updateBps(corpID)
				self.updateCorpAssets(corpID)
				self.updateMoonMining(corpID)
				self.updateContracts(corpID)
				self.updateOfficeFlags()
				self.updateDivisions(corpID)
				self.updatePrices()
				self.updateProduction()
				self.updateStructures(corpID)
				self.updateTranslations()
				break
			if "Factory_Manager" in baseroles and self.config.getConfig()["server"]["debug"]:
				self.updateIndustryJobs(corpID)
				self.updateOfficeFlags()
				self.updatePrices()
				# self.updateContracts(corpID)
				self.updateProduction()
				self.updateTranslations()
		print("Finished update")
		self.isRefreshing = False
		self.lastUpdate = int(time.time())
		return