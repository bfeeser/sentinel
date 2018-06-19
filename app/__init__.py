from flask import Flask
from flask_caching import Cache
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)

# instantiate cache for session memoization
cache = Cache(app, config={"CACHE_TYPE": "simple"})
cache.init_app(app)

# initialize cryptography
bcrypt = Bcrypt(app)

# initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.next_url = None

# get database configuration
app.config.from_pyfile("config.py")

from app import views, models
