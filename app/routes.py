from app import app
from flask import request, jsonify
import logging
from functools import wraps

from app.services.google_sheets_service import GoogleSheetsService
from app.task_dto import TaskDTO

# Ленивая инициализация сервиса
gs_service = None

def get_gs_service():
    global gs_service
    if gs_service is None:
        gs_service = GoogleSheetsService()
    return gs_service

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    return decorated_function

# Объединенный маршрут для создания/обновления задач
@app.route('/gh', methods=['POST'])
@handle_errors
def handle_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        task = TaskDTO(**data)
        service = get_gs_service()
        service.store_task(task)

        return jsonify({"message": "success"}), 200
    except Exception as e:
        logging.error(f"Error handling task: {str(e)}")
        return jsonify({"error": "Failed to process task"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200