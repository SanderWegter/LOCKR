from flask import Blueprint, render_template, abort, session, redirect, url_for, request
from functools import wraps
from lib.Users import Users
from time import time

from nav import navigation_bar

def requires_auth(f):
	@wraps(f)
	def decorated_auth(*args, **kwargs):
		if users.isVerified():
			user = users.getUserInfo()
		else:
			return redirect(url_for('page_routes.login', secure_uri=users.getAuthURI()))
		return f(*args, **kwargs)
	return decorated_auth

def requires_admin(f):
	@wraps(f)
	def decoracted_admin(*args, **kwargs):
		if not users.isAdmin():
			return redirect(url_for('page_routes.index'))
		return f(*args, **kwargs)
	return decoracted_admin

page_routes = Blueprint('page_routes', __name__, template_folder='templates')

@page_routes.before_request
def before_request():
	if 'username' in session:
		users.updateLastseen()
	pass

users = Users()

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
	if users.isLoggedIn():
		return redirect(url_for('page_routes.index'))
	if request.method == "POST":
		res = users.loginUser(request.form)
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
	users.checkInUser(request.args.get('code'))
	return redirect(url_for('page_routes.index'))

@page_routes.route('/logout')
@requires_auth
def logout():
	users.logoutUser()
	return redirect(url_for('page_routes.login', secure_uri=users.getAuthURI()))

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
		ts=str(int(time()))
		)