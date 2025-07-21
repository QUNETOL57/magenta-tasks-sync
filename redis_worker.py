import redis
import json
import time
from app.services.google_sheets_service import GoogleSheetsService
from app.task_dto import TaskDTO
from config import config

redis_client = redis.StrictRedis(
    host=config.get('REDIS_HOST'),
    port=config.get('REDIS_PORT'),
    db=config.get('REDIS_DB'),
    password=config.get('REDIS_PASSWORD'),
    decode_responses=True
)

# Ленивая инициализация сервиса
gs_service = None

def get_gs_service():
    global gs_service
    if gs_service is None:
        gs_service = GoogleSheetsService()
    return gs_service

def process_queue():
    while True:
        keys = redis_client.keys()
        if keys:
            service = get_gs_service()
            tasks = []
            for key in keys:
                # Получаем данные из Redis и сразу удаляем, что бы избежать потери данных
                data_json = redis_client.get(key)
                redis_client.delete(key)
                # TODO сделать валидатор
                if data_json:
                    data = json.loads(data_json)
                    task = TaskDTO(**data)
                    tasks.append(task)
            service.store_tasks_batch(tasks)

        time.sleep(5)  # Пауза между итерациями

if __name__ == '__main__':
    process_queue()