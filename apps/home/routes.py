# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from apps import kinde_client
from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound


@blueprint.route('/index')
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)
        user= kinde_client.get_user_details()
        profile_picture= user.get('picture')
        print(profile_picture)
        given_name= user.get('given_name')
        family_name= user.get('family_name')
        user_email = user.get('email')
        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, profile_picture=profile_picture, given_name=given_name, family_name=family_name, user_email=user_email)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
