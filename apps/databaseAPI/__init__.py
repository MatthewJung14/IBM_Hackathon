from flask import Blueprint

blueprint = Blueprint(
    'databaseAPI_blueprint',
    __name__,
    url_prefix='/api'
)
