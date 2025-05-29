import psutil
import logging
import signal
import os
import time
from threading import Thread

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self, memory_threshold=80, restart_callback=None):
        self.memory_threshold = memory_threshold
        self.restart_callback = restart_callback
        self.monitoring = False

    def start_monitoring(self):
        self.monitoring = True
        monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Health monitoring started")

    def stop_monitoring(self):
        self.monitoring = False
        logger.info("Health monitoring stopped")

    def _monitor_loop(self):
        while self.monitoring:
            try:
                # Проверяем использование памяти
                memory_percent = psutil.virtual_memory().percent

                if memory_percent > self.memory_threshold:
                    logger.warning(f"High memory usage: {memory_percent}%")
                    if self.restart_callback:
                        self.restart_callback()

                # Проверяем каждые 30 секунд
                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                time.sleep(60)  # Увеличиваем интервал при ошибке


def graceful_restart():
    """Функция для graceful restart воркеров"""
    try:
        # Отправляем сигнал HUP мастер-процессу gunicorn
        with open('/tmp/gunicorn.pid', 'r') as f:
            master_pid = int(f.read().strip())
        os.kill(master_pid, signal.SIGHUP)
        logger.info("Sent SIGHUP signal for graceful restart")
    except Exception as e:
        logger.error(f"Failed to restart: {e}")


# Инициализация монитора
health_monitor = HealthMonitor(memory_threshold=85, restart_callback=graceful_restart)