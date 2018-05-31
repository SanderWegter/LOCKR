from lib.Database import Database
from lib.Config import Config
from lib.ESI import ESI
from flask import session, request, url_for
from requests import get

import time
import json
import math

class Users:
	def __init__(self):
		self.db = Database()
		self.esi = ESI()
		self.config = Config()
		self.admins = self.config.getConfig()["settings"]["admins"]
		self.activity_ids = [
			"None",
			"Manufacturing",
			"Researching Tech",
			"Researching TE",
			"Researching ME",
			"Copying",
			"Duplicating",
			"Invention",
			"Reverse engineering"
		]
		self.corpCache = 0
		self.corpAssets = []
		self.itemTranslations = {}
		self.divisions = []

	def isLoggedIn(self):
		if "token" in session:
			cur = self.db.query("UPDATE users SET ip=%s, lastActive = NOW(), refreshToken = %s WHERE charID = %s",[request.remote_addr,session["token"]["refresh_token"],session["char"]["CharacterID"]])
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
			cur = self.db.query("UPDATE users SET ip=%s, lastActive = NOW(), refreshToken = %s WHERE charID = %s",[request.remote_addr,session["token"]["refresh_token"],session["char"]["CharacterID"]])
			if session["char"]["CharacterID"] in self.admins:
				session["isAdmin"] = True
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

		cur = self.db.query("SELECT ref_id,`date`,is_transaction,balance,in_out FROM wallet WHERE charID = %s ORDER BY `date` ASC",[charID])
		walletHistory = []
		old_balance = 0
		for w in cur.fetchall():
			ref_id,datestamp,is_transaction,balance,in_out = w

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
		corpID = self.getCorpID()
		citadels = set()
		itemList = set()
		industryJobs = self.esi.getESIInfo('get_corporations_corporation_id_industry_jobs', {"corporation_id": corpID})
		industry = []
		for i in industryJobs:
			if "activity_id" in i:
				i["activity_id"] = self.activity_ids[i["activity_id"]]
			if "end_date" in i:
				i["end_date"] = int(time.mktime(time.strptime(str(i["end_date"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "start_date" in i:
				i["start_date"] = int(time.mktime(time.strptime(str(i["start_date"]),'%Y-%m-%dT%H:%M:%S+00:00')))*1000
			if "blueprint_type_id" in i:
				itemList.add(i["blueprint_type_id"])
			if "installer_id" in i:
				itemList.add(i["installer_id"])
			
			if i["blueprint_location_id"] < 69999999:
				itemList.add(i["location_id"])
			else:
				citadels.add(i["location_id"])
			industry.append(i)

		itemTranslations = {}
		if len(itemList)>0:
			itemTranslation = self.esi.getESIInfo('post_universe_names', {"ids": itemList})
			for i in itemTranslation:
				itemTranslations[i['id']] = i["name"]
		if len(citadels)>0:
			for s in citadels:
				citadelInfo = self.esi.getESIInfo('get_universe_structures_structure_id',{"structure_id":s})
				if "name" in citadelInfo:
					itemTranslations[s] = citadelInfo["name"]
				else:
					itemTranslations[s] = "Unknown - No permissions"
		return {"jobs":industry, "translations": itemTranslations}

	def getCorpAssets(self):
		assets = self.corpAssets
		itemTranslations = self.itemTranslations
		divisions = self.divisions
		officeFlags = {}
		itemL = [[]]
		iL = 0
		if int(time.time() - self.corpCache) > 3600:
			self.corpCache = int(time.time())
			citadels = set()
			itemList = set()
			corpID = self.getCorpID()
			cur = self.db.query("SELECT charID,refreshToken FROM users WHERE LENGTH(refreshToken) > 2")
			for r in cur.fetchall():
				charID,refreshToken = r
				self.esi.subToken(refreshToken)
				t = self.esi.getForceRefresh()
				roles = self.esi.getESIInfo('get_characters_character_id_roles',{"character_id": charID})
				baseroles = roles["roles"]
				if "Director" in baseroles:
					page = 1
					hasMorePages = True
					while hasMorePages:
						assetList = self.esi.getESIInfo('get_corporations_corporation_id_assets', {"corporation_id": corpID, "page": page})
						if len(assetList) == 0:
							hasMorePages = False
							continue
						for asset in assetList:
							if asset["location_id"] < 69999999:
								itemList.add(asset["location_id"])
							else:
								citadels.add(asset["location_id"])

							if asset["location_flag"] == "OfficeFolder" or "CorpSAG" in asset["location_flag"]:
								officeFlags[asset["item_id"]] = asset["location_id"]
							if asset["type_id"] < 69999999:
								itemList.add(asset["type_id"])
							else:
								citadels.add(asset["type_id"])
							assets.append(asset)
						page += 1

					divisions = self.esi.getESIInfo('get_corporations_corporation_id_divisions',{"corporation_id": corpID})

					continue
			
			for a in assets:
				if a["location_id"] in officeFlags:
					a["location_id"] = officeFlags[a["location_id"]]
					if a["location_id"] < 69999999:
						itemList.add(a["location_id"])
					else:
						citadels.add(a["location_id"])

			itemTranslations = {}
			if len(itemList) > 0:
				itemTranslation = self.esi.getESIInfo('post_universe_names', {"ids": itemList})
				for i in itemTranslation:
					itemTranslations[i['id']] = i["name"]
			if len(citadels)>0:
				for s in citadels:
					citadelInfo = self.esi.getESIInfo('get_universe_structures_structure_id',{"structure_id":s})
					if "name" in citadelInfo:
						itemTranslations[s] = citadelInfo["name"]
					else:
						itemTranslations[s] = "Unknown - No permissions"
		self.corpAssets = assets
		self.itemTranslations = itemTranslations
		self.divisions = divisions			
		return {"assets": assets, "translations": itemTranslations, "divisions": divisions}