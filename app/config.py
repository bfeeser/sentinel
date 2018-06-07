import os

app_dir = os.path.abspath(os.path.dirname(__file__))

EMAIL_USERNAME = "sentinel.alerts.sys"
EMAIL_FROM = EMAIL_USERNAME + "@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

WTF_CSRF_ENABLED = True
SECRET_KEY = "96b0ea7500480ff5ea541b238d8733e9"
