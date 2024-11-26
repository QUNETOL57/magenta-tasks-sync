import logging

from app import app
from flask import request, jsonify


@app.route('/yandex/create', methods=['POST'])
def create_yandex():
    data = request.get_json()
    return jsonify({"message": "success"}), 200


@app.route('/yandex/update', methods=['POST'])
def update_yandex():
    data = request.get_json()
    return jsonify({"message": "success"}), 200
