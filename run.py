from app import app
import logging

from app.health_monitor import health_monitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def make_shell_context():
    return dict(app=app)


if __name__ == '__main__':
    # Запускаем мониторинг здоровья
    health_monitor.start_monitoring()

    port = app.config.get('PORT', 5001)
    app.run(host='0.0.0.0', port=port, debug=False)