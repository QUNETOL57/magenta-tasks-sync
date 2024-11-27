import logging
import os

from flask import Flask, request

app = Flask(__name__)
app.config.from_object('config.' + (os.environ.get('FLASK_ENV') or 'Dev'))

logging.basicConfig(level=logging.INFO, filename="logs/app.log", filemode="w",
                    format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d.%m.%Y %H:%M:%S")


@app.before_request
def log_request_info():
    logging.info(f"Request: {request.method} {request.url} - Params: {request.args} - Body: {request.get_json()}")


@app.after_request
def log_response_info(response):
    logging.info(f"Response: {response.status} - Data: {response.get_data(as_text=True)}")
    return response


with app.app_context():
    from . import routes, task_dto
