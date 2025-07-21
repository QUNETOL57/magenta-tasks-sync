from app import app

from app.health_monitor import health_monitor
from logging_config import listener


def make_shell_context():
    return dict(app=app)


if __name__ == '__main__':
    try:
        # Запускаем мониторинг здоровья
        health_monitor.start_monitoring()

        port = app.config.get('PORT', 5001)
        app.run(host='0.0.0.0', port=port, debug=False)
    finally:
        listener.stop()
