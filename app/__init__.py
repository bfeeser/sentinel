"""
Ben Feeser
Sentinel

Initializes application.
"""
from flask import Flask
from flask.ext.cache import Cache
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from config import connect_db

# define flask app
app = Flask(__name__)

# instantiate cache for session memoization
cache = Cache(app, config={"CACHE_TYPE": "simple"})
cache.init_app(app)

# initialize cryptography
bcrypt = Bcrypt(app)

# initialize Login Manager
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"
lm.login_message_category = "info"
lm.next_url = None

# get database configuration
app.config.from_pyfile("config.py")

db, cursor = connect_db()

from app import views, models
