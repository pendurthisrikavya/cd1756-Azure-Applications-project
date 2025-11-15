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

# FIXED: Correct constructor
app = Flask(__name__)
app.config.from_object(Config)

# Log Format
LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'

# Stream logs to stdout (Azure Log Stream reads from stdout)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

handlers = [stream_handler]

# Optional file logging (Azure enables this only if storage is on)
if os.environ.get("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false").lower() == "true":
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(file_handler)

# Attach all handlers to app logger
for h in handlers:
    app.logger.addHandler(h)

app.logger.setLevel(logging.INFO)
app.logger.info("Flask app initialized and logging configured.")

# Flask extensions
Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# Import views LAST
import FlaskWebProject.views
