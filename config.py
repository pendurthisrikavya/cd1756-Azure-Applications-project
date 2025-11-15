import os
import urllib.parse

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):

    # Flask Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or "secret-key"

    # Azure Blob Storage
    BLOB_ACCOUNT = os.environ.get('BLOB_ACCOUNT') or "images17"
    BLOB_STORAGE_KEY = os.environ.get('BLOB_STORAGE_KEY')
    BLOB_CONTAINER = os.environ.get('BLOB_CONTAINER') or "images"
    BLOB_CONNECTION_STRING = os.environ.get('BLOB_CONNECTION_STRING')

    # Azure SQL Database
    SQL_SERVER = os.environ.get('SQL_SERVER')
    SQL_DATABASE = os.environ.get('SQL_DATABASE')
    SQL_USER_NAME = os.environ.get('SQL_USER_NAME')
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD')

    # URL encode username/password
    _user = urllib.parse.quote_plus(SQL_USER_NAME)
    _password = urllib.parse.quote_plus(SQL_PASSWORD)

    # Correct SQLAlchemy URI
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{_user}:{_password}@{SQL_SERVER}:1433/{SQL_DATABASE}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Microsoft Authentication (friend-style hardcoded)
    CLIENT_ID = "987a9272-53d5-4d39-9baa-7d1222688038"
    CLIENT_SECRET = "Owv8Q~69m2ELP~icBC1pBHnaJzdgHq6T.xm9Ga1f"

    AUTHORITY = "https://login.microsoftonline.com/common"

    # Must match Azure AD Redirect URI
    REDIRECT_PATH = "/getAToken"

    # Microsoft Graph scopes
    SCOPE = ["User.Read"]

    SESSION_TYPE = "filesystem"
