from flask import Blueprint, render_template, abort, session, redirect, url_for, request
from functools import wraps
from lib.Functions import Functions
from time import time

from nav import navigation_bar

from apscheduler.scheduler import Scheduler

sched = Scheduler()
sched.start()

functions = Functions()

def testUpdate():
	functions.updateAllData()

job = sched.add_cron_job(testUpdate, minute="*/10")

def requires_auth(f):
	@wraps(f)
	def decorated_auth(*args, **kwargs):
		if functions.isVerified():
			functions.getUserInfo()
		else:
			return redirect(url_for('page_routes.login', secure_uri=functions.getAuthURI()))
		return f(*args, **kwargs)
	return decorated_auth

def requires_admin(f):
	@wraps(f)
	def decoracted_admin(*args, **kwargs):
		if not functions.isAdmin():
			return redirect(url_for('page_routes.index'))
		return f(*args, **kwargs)
	return decoracted_admin

page_routes = Blueprint('page_routes', __name__, template_folder='templates')

#Main routes
@page_routes.route('/')
@requires_auth
def index():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	return render_template(
		'index.html',
		title="Dashboard",
		notification=notification,
		navigation_bar=navigation_bar,
		ts=str(int(time()))
		)

@page_routes.route('/assets')
@requires_auth
@requires_admin
def assets():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	return render_template(
		'corpassets.html',
		title="Corp Assets",
		notification=notification,
		navigation_bar=navigation_bar,
		ts=str(int(time()))
		)

@page_routes.route('/pricing')
@requires_auth
def pricing():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	return render_template(
		'pricing.html',
		title="Pricing Lookup",
		notification=notification,
		navigation_bar=navigation_bar,
		ts=str(int(time()))
		)

@page_routes.route('/mining')
@requires_auth
def mining():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	return render_template(
		'mining.html',
		title="Mining",
		notification=notification,
		navigation_bar=navigation_bar,
		ts=str(int(time()))
		)

@page_routes.route('/contracts')
@requires_auth
def contracts():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	return render_template(
		'contracts.html',
		title="Contracts",
		notification=notification,
		navigation_bar=navigation_bar,
		ts=str(int(time()))
		)

@page_routes.route('/login', methods=["GET","POST"])
def login():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	if functions.isLoggedIn():
		return redirect(url_for('page_routes.index'))
	if request.method == "POST":
		res = functions.loginUser(request.form)
		if not res:
			return redirect(url_for('page_routes.index'))
	return render_template(
		'login.html',
		title='Login',
		notification=notification,
		navigation_bar=navigation_bar,
		secure_uri=request.args["secure_uri"],
		ts=str(int(time()))
		),401

@page_routes.route('/oauth')
def oauth():
	functions.checkInUser(request.args.get('code'))
	return redirect(url_for('page_routes.index'))

@page_routes.route('/logout')
@requires_auth
def logout():
	functions.logoutUser()
	return redirect(url_for('page_routes.login', secure_uri=functions.getAuthURI()))

@page_routes.route('/admin')
@requires_auth
@requires_admin
def admin():
	notification = {}
	if "notification" in session:
		notification = {
			"message": session["notification"],
			"type": session["notificationtype"]
		}
		session.pop("notification")
		session.pop("notificationtype")
	return render_template(
		'admin.html',
		title="Admin page",
		navigation_bar=navigation_bar,
		notification=notification,
		ts=str(int(time()))
		)