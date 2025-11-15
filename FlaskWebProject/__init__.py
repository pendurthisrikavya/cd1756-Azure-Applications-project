"""
The flask application package.
"""
import logging
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
import os, sys
from logging.handlers import RotatingFileHandler

app = Flask(_name_)
app.config.from_object(Config)
# TODO: Add any logging levels and handlers with app.logger
# Format used in Log Stream
LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'

# 1) Stream logs to stdout (Azure Log Stream reads this)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# 2) Optional: also write to a rolling file if storage is enabled
handlers = [stream_handler]
if os.environ.get("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false").lower() == "true":
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(file_handler)

# Attach handlers and set level
for h in handlers:
    app.logger.addHandler(h)
app.logger.setLevel(logging.INFO)

app.logger.info("Flask app initialized and logging configured.")
Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

import FlaskWebProject.views
