import os
import MySQLdb

# app config
app_dir = os.path.abspath(os.path.dirname(__file__))

# email config
EMAIL_USERNAME = "sentinel.alerts.sys"
EMAIL_FROM = EMAIL_USERNAME + "@gmail.com"
EMAIL_PASSWORD = "horsebridgenose"

# wtform config
WTF_CSRF_ENABLED = True
SECRET_KEY = "96b0ea7500480ff5ea541b238d8733e9"

# db config
DB_HOST = "localhost"
DB_PORT = None
DB = "sentinel"
DB_USERNAME = "jharvard"
DB_PASSWORD = "crimson"


def connect_db(**kwargs):
    # function to connect to database
    # returns tuple of db and cursor object
    params = {}
    params["charset"] = "utf8"
    params["connect_timeout"] = 10
    params["db"] = DB
    params["host"] = DB_HOST
    params["local_infile"] = 1
    params["user"] = DB_USERNAME
    params["passwd"] = DB_PASSWORD

    # override params
    params.update(**kwargs)

    # connect to database
    db = MySQLdb.connect(**params)
    cursor = db.cursor()

    return db, cursor
