from flask import Blueprint

blueprint = Blueprint(
    'chatbotAPI_blueprint',
    __name__,
    url_prefix='/chat'
)
