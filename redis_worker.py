import redis
import json
import time
from app.services.google_sheets_service import GoogleSheetsService
from app.task_dto import TaskDTO
from config import config
from gspread.exceptions import APIError
from logging_config import logger

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
        try:
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
                
                if tasks:
                    logger.info(f"Processing {len(tasks)} tasks from Redis queue")
                    service.store_tasks_batch(tasks)
                    logger.info(f"Successfully processed {len(tasks)} tasks")
            
            time.sleep(30)  # Пауза между итерациями увеличена до 30 секунд
            
        except APIError as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                logger.warning(f"API quota exceeded, waiting 60 seconds before retry: {e}")
                time.sleep(60)  # Ждем 60 секунд при превышении квоты
            else:
                logger.error(f"Google Sheets API error: {e}")
                time.sleep(30)
        except Exception as e:
            logger.error(f"Unexpected error in process_queue: {e}")
            time.sleep(30)

if __name__ == '__main__':
    process_queue()