import logging

from app import app
from flask import request, jsonify


@app.route('/yandex/create', methods=['POST'])
def create_yandex():
    data = request.get_json()
    # logging.info("create")
    return jsonify({"message": "Создание в ЯТ", "data": data}), 200


@app.route('/yandex/update', methods=['POST'])
def update_yandex():
    data = request.get_json()
    # logging.info("update")
    return jsonify({"message": "Обновление в ЯТ", "data": data}), 200
