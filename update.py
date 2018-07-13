from lib.Database import Database
from lib.Config import Config
from lib.ESI import ESI
#from lib.Functions import Functions

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

    def updateAll(self):
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
            exit()

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
            print(baseroles)
            if "Director" in baseroles:
                jobs = self.updateIndustryJobs(corpID)
                bps = self.updateBps(corpID)
                assets = self.updateCorpAssets(corpID)
                moon = self.updateMoonMining(corpID)
                contracts = self.updateContracts(corpID)
                flags = self.updateOfficeFlags()
                divisions = self.updateDivisions(corpID)
                prices = self.updatePrices()
                production = self.updateProduction()
                structures = self.updateStructures(corpID)
                translations = self.updateTranslations()
                a = {
                    "jobs": jobs, 
                    "bps": bps, 
                    "assets": assets[0], 
                    "moon": moon, 
                    "contracts": contracts, 
                    "flags": flags, 
                    "divisions": divisions, 
                    "prices": prices, 
                    "production": production[0], 
                    "toproduce": production[1],
                    "structures": structures, 
                    "translations": translations,
                    "assetnames": assets[1]
                }
                print(a['jobs'])
                for i in a:
                    cur = self.db.query("DELETE FROM autoupdate WHERE type = %s",[i])
                    cur = self.db.query("INSERT INTO autoupdate (`type`,`json`) VALUES (%s,%s)",[i,json.dumps(a[i])])
                with open('tempstore/translations.json','w') as f:
                    f.write(json.dumps(translations))
                with open('tempstore/bps.json','w') as f:
                    f.write(json.dumps(bps))
                with open('tempstore/assets.json', 'w') as f:
                    f.write(json.dumps(assets[0]))
                break
            if "Factory_Manager" in baseroles and self.config.getConfig()["server"]["debug"]:
                jobs = self.updateIndustryJobs(corpID)
                flags = self.updateOfficeFlags()
                prices = self.updatePrices()
                # updateContracts(corpID)
                production = self.updateProduction()
                translations = self.updateTranslations()
                a = {
                    "jobs": jobs, 
                    "bps": {}, 
                    "assets": [], 
                    "moon": {}, 
                    "contracts": {}, 
                    "flags": flags, 
                    "divisions": [], 
                    "prices": prices, 
                    "production": production[0], 
                    "toproduce": production[1],
                    "structures": {}, 
                    "translations": translations,
                    "assetnames": []
                }
                for i in a:
                    cur = self.db.query("DELETE FROM autoupdate WHERE type = %s",[i])
                    cur = self.db.query("INSERT INTO autoupdate (`type`,`json`) VALUES (%s,%s)",[i,json.dumps(a[i])])
                with open('tempstore/translations.json','w') as f:
                    f.write(json.dumps(translations))
                with open('tempstore/bps.json','w') as f:
                    f.write(json.dumps(bps))
            print("Finished update")
            self.isRefreshing = False
            self.lastUpdate = int(time.time())
        return

    def updateIndustryJobs(self, corpID):
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
        return industry

    def updateBps(self, corpID):
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
        return bps

    def updateDivisions(self, corpID):
        divisions = self.divisions
        divisions = self.esi.getESIInfo('get_corporations_corporation_id_divisions',{"corporation_id": corpID})
        self.divisions = divisions
        return divisions

    def updateCorpAssets(self, corpID):
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
        return [nw,self.assetNames]

    def updateContracts(self, corpID):
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
        return contracts

    def updateMoonMining(self, corpID):
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
        return self.mining
    
    def updateTranslations(self):
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

        return self.itemTranslations
        
    def updateOfficeFlags(self):
        for k in self.officeFlags:
            try:
                self.officeFlags[k] = self.officeFlags[self.officeFlags[k]]
            except:
                pass
        return self.officeFlags

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
            bpItemID = self.esi.getESIInfo('post_universe_ids', {"names": [itemTranslations[p]["name"]+" Blueprint"]})
            print(itemTranslations[p]["name"])
            print(bpItemID)

            #bpItemID = self.esi.getESIInfo('get_search',{'strict': 'true', 'search': itemTranslations[p]["name"]+" Blueprint", 'categories': "inventory_type"})
            try:
                cur = self.db.query("SELECT COUNT(*) FROM itemLookup WHERE idnum = %s",[bpItemID["inventory_types"][0]["id"]])
                if cur.fetchone()[0] == 0:
                    cur = self.db.query("INSERT INTO itemLookup (`idnum`,`name`,`marketGroup`) VALUES (%s,%s,%s)",[bpItemID["inventory_types"][0]["id"],itemTranslations[p]["name"]+" Blueprint","Blueprints"])
            except:
                print("No bp? "+itemTranslations[p]["name"])
                print(bpItemID)
                pass
            try:
                bpID = bpItemID["inventory_types"][0]["id"]
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
        return self.prices

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
            print(r.status_code)
            print(r.text)
            marketInfo = r.json()
            
            for r in marketInfo:
                print(r)
                typeID = r["buy"]["forQuery"]["types"][0]
                buy = r["buy"]["fivePercent"]
                sell = r["sell"]["fivePercent"]
                cur = self.db.query("UPDATE priceLookup SET iskBuy = %s, iskSell = %s WHERE typeID = %s",[buy,sell,typeID])
        return {}

    def updateProduction(self):
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
            #bpItemID = self.esi.getESIInfo('get_search',{'strict': 'true', 'search': itemTranslations[p]["name"]+" Blueprint", 'categories': "inventory_type"})
            bpItemID = self.esi.getESIInfo('post_universe_ids', {"names": [itemTranslations[p]["name"]+" Blueprint"]})
            print(itemTranslations[p]["name"]+" Blueprint")
            print(bpItemID)
            prodBP = prodBP + (bpItemID["inventory_types"][0]["id"],)
            self.toProduce[bpItemID["inventory_types"][0]["id"]] = {'quantity': self.toProduce[p], 'dbid': p}

        format_strings = ','.join(['%s'] * len(prodBP))
        print(format_strings)
        print(prodBP)
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
        return [prodMats, self.toProduce]

    def updateStructures(self, corpID):
        print("Structures")
        return {}

f = Functions()
f.updateAll()