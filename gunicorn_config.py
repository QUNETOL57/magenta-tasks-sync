import multiprocessing

# Основные настройки
bind = "0.0.0.0:5555"
workers = min(multiprocessing.cpu_count(), 4)  # Ограничиваем количество воркеров
worker_class = "sync"

# Таймауты
timeout = 300  # Увеличиваем таймаут до 5 минут
keepalive = 5
graceful_timeout = 30

# Память и производительность
max_requests = 1000  # Перезапуск воркера после 1000 запросов
max_requests_jitter = 100  # Добавляем случайность
worker_tmp_dir = "/dev/shm"  # Используем RAM для временных файлов

# Логирование
accesslog = "app.log"
errorlog = "error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Перезапуск воркеров
preload_app = False  # Отключаем preload для избежания проблем с памятью
worker_connections = 1000

# Мониторинг
enable_stdio_inheritance = True

# Обработка сигналов для graceful restart
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)