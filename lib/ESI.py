from lib.Database import Database
from lib.Config import Config
from esipy import App, EsiClient, EsiSecurity
from esipy.exceptions import APIException
from flask import session

class ESI:
	def __init__(self):
		self.db = Database()
		self.config = Config()
		self.scopes = self.config.getConfig()["settings"]["esiScopes"]
		self.esi_app = App.create(
			url=self.config.getConfig()["settings"]["esiURL"],
		)
		self.security = EsiSecurity(
			app=self.esi_app,
			redirect_uri=self.config.getConfig()["settings"]["esiCallback"],
			client_id=self.config.getConfig()["settings"]["esiClientID"],
			secret_key=self.config.getConfig()["settings"]["esiSecretKey"]
		)
		self.client = EsiClient(
			security=self.security,
			retry_requests=True,
			header={'User-Agent': self.config.getConfig()["settings"]["esiCustomHeader"]}
		)

	def getAuthURI(self):
		return self.security.get_auth_uri(scopes=self.scopes)

	def getToken(self, code):
		return self.security.auth(code)

	def getESIChar(self, token):
		self.security.update_token(token)
		self.security.refresh()
		return self.security.verify()

	def isVerified(self, token):
		try:
			self.security.update_token(token)
		except:
			return False

		try:
			self.security.refresh()
			character = self.security.verify()
		except:
			return False
		session["char"] = character
		return True

	def getESIInfo(self, endpoint, obj):
		info = self.esi_app.op[endpoint](**obj)
		res = self.client.request(info)
		return res.data

	def subToken(self, refresh_token):
		self.security.update_token({
			'access_token': '',  
			'expires_in': -1,
			'refresh_token': refresh_token
		})

	def getForceRefresh(self):
		return self.security.refresh()