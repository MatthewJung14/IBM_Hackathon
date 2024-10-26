# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from functools import wraps

from flask import render_template, redirect, request, url_for, session, current_app
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from apps import db, login_manager, kinde_client, user_clients
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

from apps.authentication.util import verify_pass


def get_authorized_data(kinde_client):
    user = kinde_client.get_user_details()
    return {
        "id": user.get("id"),
        "user_given_name": user.get("given_name"),
        "user_family_name": user.get("family_name"),
        "user_email": user.get("email"),
        "user_picture": user.get("picture"),
    }

def is_user_authenticated():
    if session.get("user"):
        kinde_client = user_clients.user_clients.get(session.get("user"))
        if kinde_client and kinde_client.is_authenticated():
            return True
    return False


def kinde_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_user_authenticated():
            return redirect(url_for('authentication_blueprint.login'))
        return f(*args, **kwargs)
    return decorated_function



@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@blueprint.route('/login')
def login():
    return redirect(kinde_client.get_login_url())

@blueprint.route('/register')
def register():
    return redirect(kinde_client.get_register_url())

@blueprint.route('/callback')
def callback():
    print(request.url)
    kinde_client.fetch_token(authorization_response=request.url)
    data = {}
    data.update(get_authorized_data(kinde_client))
    session["user"] = data.get("id")
    user_clients[data.get("id")] = kinde_client
    return redirect(url_for("home_blueprint.index"))

@blueprint.route('/logout')
def logout():
    user_id = session.get("user")
    if user_id:
        user_clients.pop(user_id, None)
    session.pop("user", None)
    return redirect(kinde_client.logout(redirect_to=url_for('authentication_blueprint.login')))



# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
