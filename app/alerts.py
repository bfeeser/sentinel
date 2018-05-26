#!/home/jharvard/vhosts/sentinel/flask/bin/python
"""
Ben Feeser
Sentinel

Library to easily configure and send alerts;
can send attachements as well.
"""

import smtplib
import mimetypes
import os
import logging
import config
import tornado.options
from email import encoders
from processes import get_logs
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText


def get_scheduled_patterns():
    # connects to db to get all scheduled alerts
    (db, cursor) = config.connect_db()

    # use tornado logging and option parsing
    tornado.options.parse_command_line()

    logging.info("starting sentinel alerts")

    # get scheduled alerts based on day of week and current time
    cursor.execute(
        """
        SELECT
            a.name, a.recipients, a.pattern,
            h.path, h.host, h.host_user
        FROM patterns a
        JOIN hosts h
            ON h.id = a.host
        WHERE a.schedule_days LIKE
            CONCAT('%', WEEKDAY(CURDATE()), '%')
            AND a.schedule_time = SUBSTRING(CURTIME(), 1, 5)
        AND a.recipients IS NOT NULL
        """
    )

    logging.info("found {} alerts".format(cursor.rowcount))

    success = 0
    errors = 0
    for (
        name,
        recipients,
        pattern,
        path,
        host,
        host_user,
    ) in cursor.fetchall():
        # for each scheduled alert get results and send it
        # override path to full path for cron
        path = config.app_dir[:-3] + path

        try:
            send(
                email_to=recipients,
                html=get_logs(path, pattern, host, host_user, alert=True),
                subject="Sentinel Alert: {}".format(name),
            )
        except Exception as e:
            # log failed alerts
            logging.error(e)
            errors += 1
        else:
            # track successful
            success += 1

    # log successes and errors
    logging.info("successfully sent {} alerts".format(success))
    if errors:
        logging.warning("{} alerts encountered errors".format(errors))

    # close connection
    logging.info("finished")
    db.close()


def send(**kwargs):
    # method send() takes an email_to, a subject,
    # a message, and can be supplied an attachement. adapted from
    # https://docs.python.org/2.6/library/email-examples.html

    # get email_to
    email_to = kwargs.get("email_to")

    if not email_to:
        raise RuntimeError("send() requires an email_to")

    html = kwargs.get("html")
    text = kwargs.get("text")

    if not html and not text:
        raise RuntimeError("send() requires html or text")

    if html:
        # attach alternative text if HTML not viewable
        msg = MIMEMultipart("alternative")
        if text:
            msg.attach(MIMEText(text, "plain"))

        # attach HTML
        msg.attach(MIMEText(html, "html"))
    else:
        # send plain text message
        msg = MIMEMultipart()
        msg.attach(MIMEText(text, "plain"))

    # set from, to, and subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = email_to
    msg["Subject"] = kwargs.get("subject", "")

    # attachment must be supplied as a path to file, eg. path\to\file.foo
    attachment = kwargs.get("attachment")

    if attachment:
        attachment = os.path.join(str(attachment))

        # parse attachment's encoding; only handles text and binary
        (ctype, encoding) = mimetypes.guess_type(attachment)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"

        (maintype, subtype) = ctype.split("/", 1)

        if maintype == "text":
            # add text attachement
            fp = open(attachment)
            attachment = MIMEText(fp.read(), _subtype=subtype)
            fp.close()

        else:
            # add binary attachment
            fp = open(attachment, "rb")

            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(fp.read())

            fp.close()
            encoders.encode_base64(attachment)

        # add attachment notice in header and add to msg
        attachment.add_header(
            "Content-Disposition", "attachment", filename=attachment
        )

        msg.attach(attachment)
    # connect to gmail and send message
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
    server.sendmail(config.EMAIL_FROM, email_to.split(","), msg.as_string())
    server.quit()


if __name__ == "__main__":
    get_scheduled_patterns()
