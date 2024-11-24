import logging
import os

from flask import Flask

app = Flask(__name__)
app.config.from_object('config.' + (os.environ.get('FLASK_ENV') or 'Dev'))
logging.basicConfig(level=logging.INFO, filename="app.log",filemode="w")

with app.app_context():
    from . import routes
