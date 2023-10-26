from flask import Flask
from flask_cors import CORS
from .routes import main

def setup():
    app = Flask(__name__)
    CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    app.register_blueprint(main)
    return app