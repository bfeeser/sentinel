from flask import Flask
from flask_assets import Environment, Bundle
from flask_caching import Cache
from flask_compress import Compress
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_pyfile("config.py")

# gzip requests
compress = Compress(app)

# session memoization
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# cryptography
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.next_url = None

assets = Environment(app)

js = Bundle(
    "js/jquery-2.1.3.min.js",
    "js/bootstrap.min.js",
    "js/bootstrap-table.min.js",
    "js/scripts.js",
    filters="jsmin",
    output="gen/all.js",
)
assets.register("all_js", js)

css = Bundle(
    "css/bootstrap.min.css",
    "css/bootstrap-table.min.css",
    "css/style.css",
    filters="cssmin",
    output="gen/all.css",
)
assets.register("all_css", css)

from app import views, models
