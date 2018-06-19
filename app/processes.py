"""
get_processes(): Returns JSON data from a hosts's process list
get_logs(): Returns JSON of log data from host
get_patterns(): Returns JSON of pattern data from database
HTML Helpers: format JSON into HTML
"""

import os
import re
import socket
import psutil
import simplejson as json
import subprocess
from flask import Response, abort
from .forms import day_map


def jsonify(obj):
    """ Method to override Flask's jsonify """
    return Response(json.dumps(obj), mimetype="application/json")


def connect(host, username, port=None):
    """ Connects to a remote host via SSH """

    # do not connect if we are already connected
    if host == socket.gethostname() or host == "localhost":
        return

    cmd = ["ssh"]
    if port:
        cmd.append("-p" + str(port))

    # concat username and host
    cmd.append(f"{username}@{host}")

    subprocess.check_call(cmd)


def get_processes(host, username, port=None):
    """ Returns a JSON of process data from host """

    connect(host, username, port)

    # create status map
    # http://getbootstrap.com/css/#buttons
    # https://pythonhosted.org/psutil/#constants
    status_map = {
        "success": {"running"},
        "info": {"waiting", "waking", "sleeping", "disk_sleep"},
        "warning": {"locked", "idle", "stopped", "tracing_stop"},
        "danger": {"dead", "zombie", "wake_kill"},
    }

    # while connected to host iterate through processes
    # https://pythonhosted.org/psutil/#psutil.process_iter
    processes = []
    for proc in psutil.process_iter():
        try:
            # get process info
            pinfo = proc.as_dict(
                attrs=[
                    "pid",
                    "username",
                    "cmdline",
                    "cpu_percent",
                    "memory_percent",
                    "status",
                ]
            )
        except psutil.NoSuchProcess:
            # if the process doesn't exist any more, proceed
            continue

        try:
            # clean up output
            # round cpu and mem percentages
            pinfo["cpu_percent"] = round(pinfo["cpu_percent"], 1)
            pinfo["memory_percent"] = round(pinfo["memory_percent"], 1)

            # turn cmdline into string from list
            pinfo["cmdline"] = " ".join(pinfo["cmdline"])
        except TypeError:
            continue

        # create fancy status label using status map
        for status in list(status_map.keys()):
            if pinfo["status"] in status_map[status]:
                pinfo["status"] = get_label(status, pinfo["status"].title())

        # add process to list of processes
        processes.append(pinfo)

    return jsonify(processes)


def get_logs(path, pattern, host, username, port=None, alert=False):
    """ Returns JSON / HTML of log data from host """

    connect(host, username, port)

    # validate path
    try:
        files = os.listdir(path)
    except Exception:
        # return not found; invalid path
        return abort(404)

    logs = []
    # list logs in provided path
    for f in files:
        # check that file exists
        if os.path.isfile(os.path.join(path, f)):
            logs.append(os.path.join(path, f))

    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except Exception:
        # return bad request if unable to compile pattern
        return abort(400)

    log_status = []
    for log in logs:
        # default to no match
        button_text = "No Match"
        matches = []
        # open file and loop through lines
        try:
            f = open(log, "r")
        except Exception:
            # if open fails, skip file
            continue

        # save content of entire log file
        log_content = []
        while True:
            line = f.readline()
            if not line:
                break

            log_content.append(line)

            # match text to compiled pattern
            if compiled.findall(line):
                # we found a match, record it
                matches.append(f"<p>{line}</p>")
                button_text = "Match"

        f.close()

        # parse log name from path
        log = log.split("/")[-1]

        if not alert:
            # process logs in modal form for log view
            # get links to content and matches; stored in modals
            button_type = "success" if button_text == "Match" else "default"
            matches_link = get_button(
                button_type, button_text, "Matches-" + log
            )
            content_link = get_anchor("Content-" + log, log)

            log_status.append(
                {
                    "log": content_link
                    + get_modal("Content", log, log_content),
                    "status": matches_link
                    + get_modal("Matches", log, matches),
                    "match": button_text,
                }
            )
        else:
            # process logs into list of lists for alerts
            log_status.append((log, button_text, get_paragraph(matches)))

    if not alert:
        return jsonify(log_status)
    else:
        # return alert html: header and get_table
        html = f""" <html><body>
               e <h2>Sentinel Alert</h2>
                <h4>Host: {host}</h4>
                <h4>Path: {path}</h4>
                <h4>Pattern: {pattern}</h4>
                <br/>
            """

        html += get_table(keys=("Log", "Status", "Output"), data=log_status)

        html += "</body></html>"

        return html


def get_patterns(cursor, user_id):
    # get a user's patterns for view
    cursor.execute(
        """ SELECT
                p.id,
                p.name,
                p.pattern,
                p.recipients,
                p.schedule_days,
                p.schedule_time,
                p.updated_ts,
                h.host,
                h.host_user,
                h.path
            FROM patterns p
            JOIN hosts h
                ON h.id = p.host
            WHERE p.user = %s
        """,
        (user_id),
    )
    # patterns list
    patterns = []
    # get query columns
    cols = [i[0] for i in cursor.description]
    for row in cursor.fetchall():
        # create pattern dict
        pattern = dict(zip(cols, row))

        # create name anchor tag
        pattern[
            "name"
        ] = f"<a href=logs?pattern_id={pattern['id']}>{pattern['name']}</n>"

        # ensure datetime objects are strings
        # (they cannot be jsonified)
        pattern["updated_ts"] = str(pattern["updated_ts"])
        if pattern["schedule_time"]:
            pattern["schedule_time"] = str(pattern["schedule_time"])

        # map day numbers to abbrevs
        schedule_days = []
        if pattern["schedule_days"]:
            for n in pattern["schedule_days"]:
                schedule_days.append(day_map[n])

        pattern["schedule_days"] = ", ".join(schedule_days)

        # append patten to list
        patterns.append(pattern)

    return jsonify(patterns)


def get_hosts(cursor, role_id):
    # get a role's hosts from db
    cursor.execute(
        """ SELECT h.id, h.host, h.host_user, h.path
            FROM hosts h
            JOIN role_hosts r ON h.id = r.host
            WHERE r.role = %s
        """,
        (role_id,),
    )

    return cursor.fetchall()


def get_label(label_type, text):
    # define label format
    return f'<span class="label label-{label_type}">{text}</span>'


def get_anchor(link, text):
    # define anchor format for modals
    return f'<a data-toggle="modal" data-target="#{link}">{text}</a>'


def get_button(button_type, text, link=""):
    # define button format for modals
    return f"""<button type="button"
                      data-toggle="modal"
                      data-target="#{link}"
                      class="btn btn-{button_type}">
                {text}
               </button>"""


def get_paragraph(l):
    # convert list of text lines to paragraph
    return f"<p>{'<br>'.join(l)}</p>"


def get_modal(modal_type, text, l):
    # make modal; a popup containing content of list l
    # http://getbootstrap.com/javascript/#modals
    return f""" <div id="{modal_type}-{text}" class="modal fade">
              <div class="modal-dialog modal-lg">
                <div class="modal-content">
                  <div class="modal-header">
                    <button type="button" class="close"
                        data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                    <h4 class="modal-title">{text} {modal_type}</h4>
                  </div>
                  <div class="modal-body">
                    {get_paragraph(l)}
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-default"
                        data-dismiss="modal">Close</button>
                  </div>
                </div><!-- /.modal-content -->
              </div><!-- /.modal-dialog -->
            </div><!-- /.modal -->
        """


def get_table(data, keys, nowrap=True):
    # data should be a list of lists/tuples (ie. SQL result);
    # keys should be a list of length data[0]
    if len(keys) != len(data[0]):
        raise RuntimeError(
            f"data length ({len(keys)}) != key length ({len(data[0])})"
        )

    # build data table
    out = """<table style="border-collapse: collapse;">
                <thead>
                    <tr style="text-align: center;">"""

    # set th css style
    style = ["vertical-align: top;", "text-align:left;"]

    th_style = [
        "color: #ffffff;",
        "background-color: #555555;",
        "border: 1px solid #555555;",
        'padding: 3px;"',
    ]

    th_style.extend(style)

    def build_row(tag, style, data):
        # build row using format string for tag with style

        # add no wrap
        if nowrap:
            style.append("white-space: nowrap;")

        # build tag_format
        tag_format = f'<{tag} style="{"".join(style)}">'
        tag_format += "{}" + f"</{tag}>"

        return "".join([tag_format.format(i) for i in data])

    # build table headers
    out += build_row("th", th_style, keys)
    out += "</tr></thead><tbody>"

    # set td css style
    td_style = [
        "border: 1px solid #d4d4d4;",
        "padding: 5px;",
        "padding-top: 7px;",
        "padding-bottom: 7px;",
    ]

    th_style.extend(style)

    # build table rows
    tr_format = '<tr style="background-color:{};">'

    for i, row in enumerate(data):
        # stripe table rows
        if i % 2 == 1:
            out += tr_format.format("#ffffff")
        else:
            out += tr_format.format("#f1f1f1")

        # add data to tr
        out += build_row("td", td_style, row)
        out += "</tr>"

    out += "</table>"

    return out
