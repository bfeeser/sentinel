"""
Ben Feeser
Sentinel

Library of views.
"""

from flask import (
    g,
    abort,
    url_for,
    render_template,
    redirect,
    request,
    send_from_directory,
    flash,
)
from flask_login import login_user, logout_user, current_user, login_required
from app import app, cursor, lm, bcrypt
from .processes import get_processes, get_logs, get_hosts, get_patterns
import datetime
from . import forms
from . import models
import os


@app.route("/")
@app.route("/index")
@app.route("/processes")
@login_required
def index():
    return render_template(
        "index.html",
        hosts=get_hosts(cursor, g.user.data.get("role")),
        active=0,
    )


# set global user equal to current user
# on every request
@app.before_request
def before_request():
    g.user = current_user


# redirect /favicon to /img/favicon
# http://flask.pocoo.org/docs/0.10/patterns/favicon/
@app.route("/favicon.ico")
@app.route("/img/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/img"),
        "favicon.ico",
        mimetype="img/vnd.microsoft.icon",
    )


# processes view to monitor host's processes
# similar to UNIX's top or htop
@app.route("/api/processes")
@login_required
def processes():
    if not check_params(
        request.args.get("host"), request.args.get("username")
    ):
        # report bad request
        abort(400)

    return get_processes(
        request.args.get("host"),
        request.args.get("username"),
        request.args.get("port"),
    )


# view for users patterns
@app.route("/patterns")
@login_required
def render_patterns():
    return render_template(
        "patterns.html",
        user_id=g.user.data.get("id"),
        hosts=get_hosts(cursor, g.user.data.get("role")),
        active=2,
    )


# api for users patterns
@app.route("/api/patterns")
@login_required
def patterns():
    if not check_params(request.args.get("user_id")):
        # report bad request
        abort(400)

    return get_patterns(cursor, request.args.get("user_id"))


@app.route("/register", methods=["POST", "GET"])
def register():
    # register users
    form = forms.Register()

    if form.validate_on_submit():
        # create user object
        user = models.User(email=form.email.data)

        if not user.add(form.pwd.data):
            flash("Email already exists", "danger")
            return redirect("/register")
        else:
            # successfully added user, log them in
            flash("Logged successfully.", "info")
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get("next") or url_for("index"))

    return render_template("register.html", form=form)


# creates login view
@app.route("/login", methods=["POST", "GET"])
def login():
    # create login form
    form = forms.Login()

    # check if user exists and is already authenticted
    if g.user is not None and g.user.is_authenticated():
        return redirect("/index")

    if form.validate_on_submit():
        # create user objects
        user = models.User(email=form.email.data)

        # validate email: if valid continue
        if not user.id:
            flash("Invalid email or password", "danger")
            return redirect("/login")

        # validate password: if valid log user in
        if not bcrypt.check_password_hash(
            user.data["password"], form.pwd.data
        ):
            flash("Invalid email or password", "danger")
            return redirect("/login")
        else:
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html", form=form)


# provide login manager a user loader
@lm.user_loader
def load_user(id):
    # required by flask-login to load users
    cursor.execute("SELECT email FROM users WHERE id = %s", (id,))
    if cursor.rowcount:
        # return user object
        return models.User(cursor.fetchone()[0])
    else:
        # return None if user does not exist per spec
        return None


# logs the user out
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/logs", methods=["POST", "GET"])
@login_required
def render_logs():
    # create pattern form
    form = forms.Pattern()

    # create host list
    hosts = get_hosts(cursor, g.user.data.get("role"))

    # set form path choices; they are coerced to unicode
    form.path.choices = [(str(i[0]), i[3]) for i in hosts]

    # handles load requests for patterns
    if request.args.get("pattern_id"):
        pattern = models.Pattern(request.args.get("pattern_id"))
        # if pattern requested, display associated data
        if pattern.data:
            # set form id
            form.pattern_id.data = pattern.id

            # set name and pattern
            form.name.data = pattern.data["name"]
            form.pattern.data = pattern.data["pattern"]

            # set path
            form.path.data = str(pattern.data["host"])

            # set scheduling forms
            form.recipients.data = pattern.data["recipients"]

            # set time
            if pattern.data["schedule_time"]:
                form.time.data = datetime.datetime.strptime(
                    pattern.data["schedule_time"][:-3], "%H:%M"
                )

            # set days
            if pattern.data["schedule_days"]:
                form.days.data = [d for d in pattern.data["schedule_days"]]
        else:
            # pattern not found, redirect
            return redirect("/logs")

    # handle save and delete requests for patterns
    # validate pattern
    if form.validate_on_submit():
        # fields to save for pattern
        # in order of update and create methods of Pattern class
        pattern_data = (
            form.pattern.data,
            form.name.data,
            g.user.data["id"],
            form.path.data,
            form.recipients.data,
            "".join(form.days.data),
            form.time.data,
        )

        # if pattern id provided, check that it exists
        if form.pattern_id.data:
            pattern = models.Pattern(form.pattern_id.data)
            if pattern.data:
                # if save button clicked, update
                if form.save.data:
                    pattern.update(*pattern_data)
                # if delete button clicked, update
                elif form.delete.data:
                    pattern.delete(g.user.id)
            else:
                # pattern did not exist; bad request
                flash("Pattern does not exist", "warning")
        elif form.save.data:
            # create new pattern
            pattern = models.Pattern.create(*pattern_data)

            # redirect to new pattern's page
            return redirect("/logs?pattern_id={}".format(pattern.id))
        else:
            # pattern did not exist; bad request
            flash("Pattern does not exist", "warning")

    return render_template("logs.html", hosts=hosts, form=form, active=1)


@app.route("/api/logs")
@login_required
def logs():
    if not check_params(
        request.args.get("path"),
        request.args.get("pattern"),
        request.args.get("host"),
        request.args.get("username"),
    ):
        # report bad request
        abort(400)

    return get_logs(
        request.args.get("path"),
        request.args.get("pattern"),
        request.args.get("host"),
        request.args.get("username"),
        request.args.get("port"),
    )


def check_params(*params):
    # return False if a given param is falsey
    # else return True
    for p in params:
        if not p:
            return False
    return True
