import json

from app import app
from flask import request, jsonify
import logging
from functools import wraps
import redis
from config import config


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    return decorated_function


redis_client = redis.StrictRedis(
    host=config.get("REDIS_HOST"),
    port=config.get("REDIS_PORT"),
    db=config.get("REDIS_DB"),
    password=config.get("REDIS_PASSWORD"),
    decode_responses=True
)


# Объединенный маршрут для создания/обновления задач
@app.route("/gh", methods=["POST"])
@handle_errors
def handle_task():
    try:
        data = request.get_json()
        if not data or "key" not in data:
            return jsonify({"error": "No JSON data provided"}), 400

        task_key = str(data["key"])
        # Сохраняем последнее значение по key в Redis
        redis_client.set(task_key, json.dumps(data))

        return jsonify({"message": "success"}), 200
    except Exception as e:
        logging.error(f"Error handling task: {str(e)}")
        return jsonify({"error": "Failed to process task"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200
