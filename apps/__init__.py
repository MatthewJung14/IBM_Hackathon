# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_session import Session

from kinde_sdk import Configuration
from kinde_sdk.kinde_api_client import GrantType, KindeApiClient


configuration = Configuration(host="https://findmyrelief2024.kinde.com")

kinde_api_client_params = {
    "configuration": configuration,
    "domain": "https://findmyrelief2024.kinde.com",
    "client_id": "f41b35d272fd49e1b6b7ee09e78d463c",
    "client_secret": "Z2AOsh3ipASazPpkir9MlXR7udfeZAOhmThvSNdKWqvUUDRV2m",
    "grant_type": GrantType.AUTHORIZATION_CODE,
    "callback_url": "http://localhost:5000/callback"
}
kinde_client = KindeApiClient(**kinde_api_client_params)
user_clients = {}

db = SQLAlchemy()
login_manager = LoginManager()
session = Session()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )

            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

            print('> Fallback to SQLite ')
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def setup_session(app):
    app.config['SESSION_TYPE'] = 'filesystem'
    session.init_app(app)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    app.secret_key = '3d1a555f6840b028c43f4edf4bd84b072f44567982c2622a2ac85598c76574e4'
    setup_session(app)


    return app
