import os
from dotenv import dotenv_values

config = dotenv_values()

app_dir = os.path.abspath(os.path.dirname(__file__))


class Dev:
    DEBUG = False
    PORT = 5555


class Prod:
    DEBUG = True
    PORT = 5555
