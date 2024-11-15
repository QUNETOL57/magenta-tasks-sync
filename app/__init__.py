import os

from flask import Flask

app = Flask(__name__)
app.config.from_object('config.' + (os.environ.get('FLASK_ENV') or 'Dev'))

with app.app_context():
    from . import routes
