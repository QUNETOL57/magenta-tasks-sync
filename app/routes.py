from app import app
from flask import request, jsonify

from app.services.google_sheets_service import GoogleSheetsService
from app.task_dto import TaskDTO

gs_service = GoogleSheetsService()


# Добавление новой задачи в google sheets
@app.route('/gh', methods=['POST'])
def create():
    gs_service.add_task(TaskDTO(**request.get_json()))
    return jsonify({"message": "success"}), 200


# Обновление задачи в google sheets
@app.route('/gh', methods=['PATCH'])
def update():
    gs_service.update_task(TaskDTO(**request.get_json()))
    return jsonify({"message": "success"}), 200
