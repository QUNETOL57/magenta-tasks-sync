import os

app_dir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    YANDEX_CLOUD_KEY = os.environ.get('YANDEX_CLOUD_KEY') or ''
    GOOGLE_CLOUD_KEY = os.environ.get('GOOGLE_CLOUD_KEY') or ''


class Dev(BaseConfig):
    DEBUG = True
    PORT = 5555

class Prod(BaseConfig):
    DEBUG = False