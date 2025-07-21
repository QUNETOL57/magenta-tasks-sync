import logging.handlers
import queue
from datetime import datetime
from zoneinfo import ZoneInfo

class MoscowFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo("Europe/Moscow"))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

log_queue = queue.Queue(-1)
queue_handler = logging.handlers.QueueHandler(log_queue)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(queue_handler)

file_handler = logging.FileHandler('logs/logger_app.log', encoding='utf-8')
formatter = MoscowFormatter('%(asctime)s - %(process)d - %(levelname)s - %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
file_handler.setFormatter(formatter)

listener = logging.handlers.QueueListener(log_queue, file_handler)
listener.start()