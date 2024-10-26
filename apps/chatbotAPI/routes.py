# routes.py

from flask import render_template, redirect, request, url_for, session, current_app, jsonify
from apps.chatbotAPI import blueprint


@blueprint.route('/')
def route_default():
    """
    Default route that provides a list of available API actions with their details.
    """
    available_actions = {
        "available_actions": [
            {
                "endpoint": "/donate",
                "method": "POST",
                "description": "Donate a list of items. (Updates the database)",
                "payload": {
                    "user_id": "string (256 characters)",
                    "x": "float (Longitude of the donation location)",
                    "y": "float (Latitude of the donation location)",
                    "item_location": "string (General location description)",
                    "items": "list of [item_type (string), item_amount (integer)]"
                }
            }
        ]
    }

    return jsonify(available_actions), 200




@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
