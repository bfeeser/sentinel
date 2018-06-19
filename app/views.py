import datetime
from flask import (
    g,
    abort,
    url_for,
    render_template,
    redirect,
    request,
    send_from_directory,
    session,
    flash,
)
from flask_login import login_user, logout_user, current_user, login_required
import os
from .processes import get_processes, get_logs, get_hosts, get_patterns

from app import app, login_manager, bcrypt
from db import connect, query, insert
from . import forms
from . import models


@app.route("/")
@app.route("/index")
@app.route("/processes")
@login_required
def index():
    return render_template(
        "index.html",
        hosts=get_hosts(g.cursor, g.user.data.get("role")),
        active=0,
    )


def after_this_request(func):
    if not hasattr(g, "call_after_request"):
        g.call_after_request = []
    g.call_after_request.append(func)
    return func


@app.after_request
def per_request_callbacks(response):
    for func in getattr(g, "call_after_request", ()):
        response = func(response)
    return response


@app.before_request
def before_request():
    if request.path == "/favicon.ico":
        return

    g.user = current_user
    g.db, g.cursor = connect()

    if not session.get("id"):
        insert(
            cursor=g.cursor,
            table="sessions",
            ip=request.remote_addr,
            platform=request.user_agent.platform,
            browser=request.user_agent.browser,
            version=request.user_agent.version,
            user_agent=request.user_agent.string,
            user_id=g.user.get_id(),
        )

        session["id"] = g.cursor.lastrowid

    insert(
        cursor=g.cursor,
        table="pageviews",
        referrer=request.referrer,
        url_root=request.url_root,
        path=request.full_path,
        session_id=session["id"],
        user_id=g.user.get_id(),
    )

    @after_this_request
    def cleanup(response):
        g.db.commit()
        g.db.close()
        return response


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "/static/img"),
        "favicon.ico",
        mimetype="img/vnd.microsoft.icon",
    )


@app.route("/api/processes")
@login_required
def processes():
    """ processes view to monitor host's processes
        similar to UNIX's top or htop """
    if not check_params(
        request.args.get("host"), request.args.get("username")
    ):
        abort(400)

    return get_processes(
        request.args.get("host"),
        request.args.get("username"),
        request.args.get("port"),
    )


@app.route("/patterns")
@login_required
def render_patterns():
    """ view for users patterns """
    return render_template(
        "patterns.html",
        user_id=g.user.data.get("id"),
        hosts=get_hosts(g.cursor, g.user.data.get("role")),
        active=2,
    )


@app.route("/api/patterns")
@login_required
def patterns():
    if not check_params(request.args.get("user_id")):
        abort(400)

    return get_patterns(g.cursor, request.args.get("user_id"))


@app.route("/register", methods=["POST", "GET"])
def register():
    form = forms.Register()

    if form.validate_on_submit():
        if not models.User.create(
            email=form.email.data, password=form.pwd.data
        ):
            flash("Email already exists", "danger")
            return redirect("/register")

        user = models.User(email=form.email.data)

        flash("Registered successfully.", "info")
        login_user(user, remember=form.remember_me.data)
        return redirect(request.args.get("next") or url_for("index"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = forms.Login()

    if g.user is not None and g.user.is_authenticated:
        return redirect("/index")

    if form.validate_on_submit():

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


@login_manager.user_loader
def load_user(id):
    query(g.cursor, "users", id=id)
    if g.cursor.rowcount:
        return models.User(email=g.cursor.fetchone()[1])


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/logs", methods=["POST", "GET"])
@login_required
def render_logs():
    form = forms.Pattern()

    hosts = get_hosts(g.cursor, g.user.data.get("role"))

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
        pattern_data = {
            "pattern": form.pattern.data,
            "name": form.name.data,
            "user": g.user.data["id"],
            "host": form.path.data,
            "recipients": form.recipients.data,
            "schedule_days": "".join(form.days.data),
            "schedule_time": form.time.data,
        }

        # if pattern id provided, check that it exists
        if form.pattern_id.data:
            pattern = models.Pattern(form.pattern_id.data)
            if pattern.data:
                # if save button clicked, update
                if form.save.data:
                    pattern.update(**pattern_data)
                # if delete button clicked, update
                elif form.delete.data:
                    pattern.delete(g.user.id)
            else:
                # pattern did not exist; bad request
                flash("Pattern does not exist", "warning")
        elif form.save.data:
            # create new pattern
            pattern = models.Pattern.create(**pattern_data)

            # redirect to new pattern's page
            return redirect(f"/logs?pattern_id={pattern.id}")
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
