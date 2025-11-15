"""
The flask application package.
"""
import logging
import sys
import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)

# Logging
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

handlers = [stream_handler]

if os.environ.get("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false").lower() == "true":
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(logging.INFO)
    handlers.append(file_handler)

for h in handlers:
    app.logger.addHandler(h)

app.logger.setLevel(logging.INFO)
app.logger.info("Flask app initialized and logging configured.")

Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

from FlaskWebProject import views
