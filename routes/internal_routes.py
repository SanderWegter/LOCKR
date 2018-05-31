from flask import Blueprint, render_template, abort, session, redirect, url_for, request
from functools import wraps
from lib.Users import Users
from lib.Database import Database
import json
import datetime

def requires_auth(f):
	@wraps(f)
	def decorated_auth(*args, **kwargs):
		if not users.isLoggedIn():
			return redirect(url_for('page_routes.login', secure_uri=esi.getAuthURI()))
		return f(*args, **kwargs)
	return decorated_auth

def requires_admin(f):
	@wraps(f)
	def decorated_admin(*args, **kwargs):
		if not users.isAdmin():
			return json.dumps({"error": "Unauthorized"}),401
		return f(*args, **kwargs)
	return decorated_admin

internal_routes = Blueprint('internal_routes', __name__, template_folder='templates')
users = Users()
db = Database()

@internal_routes.route("/internal/character/getWalletInfo")
@requires_auth
def getWalletInfo():
	return json.dumps(users.getWalletInfo())

@internal_routes.route("/internal/character/getMarketInfo")
@requires_auth
def getMarketInfo():
	return json.dumps(users.getMarketInfo())

@internal_routes.route("/internal/character/getSysID")
@requires_auth
def getSysID():
	return json.dumps(users.getCharSysLocID())

@internal_routes.route("/internal/industry/getAllJobs")
@requires_auth
def getIndustryJobs():
	return json.dumps(users.getIndustryJobs())

@internal_routes.route("/internal/industry/getCorpAssets")
@requires_auth
@requires_admin
def getCorpAssets():
	return json.dumps(users.getCorpAssets())

