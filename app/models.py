"""
Ben Feeser
Sentinel

Library of class models.
"""

from flask import g
from flask_login import UserMixin

from app import bcrypt
import db


class User(UserMixin):
    def __init__(self, email):
        self.data = {}
        self.email = email
        self.id = None

        db.query(g.cursor, "users", email=email)

        if g.cursor.rowcount:
            self.data = db.result_as_dict(g.cursor)

            # flask-login only accepts unicode ids
            self.id = str(self.data["id"])

    def add(self, password):
        # method to add user into db
        # returns false on failure; true on success
        try:
            db.insert(
                g.cursor,
                "users",
                email=self.data["email"],
                password=bcrypt.generate_password_hash(password),
            )
        except Exception:
            return False
        else:
            return True


class Pattern(object):
    # defines a pattern object
    # contains helper methods for retrieving assoc data

    def __init__(self, id):
        # define pattern values upon init; set to empty
        self.data = {}
        self.id = id

        # get pattern attributes from database
        db.query(g.cursor, "patterns", id=id)

        if g.cursor.rowcount:
            self.data = db.result_as_dict(g.cursor)

            # set schedule time to string; not a time object
            if self.data["schedule_time"]:
                self.data["schedule_time"] = str(self.data["schedule_time"])

    def get_host(self):
        db.query(g.cursor, "hosts", id=self.data.get("host"))

    def update(
        self,
        pattern,
        name,
        user,
        host,
        recipients,
        schedule_days,
        schedule_time,
    ):
        # function to update pattern data
        # overwrite data with provided kwargs
        self.data["pattern"] = pattern
        self.data["name"] = name
        self.data["user"] = user
        self.data["host"] = host
        self.data["recipients"] = recipients
        self.data["schedule_days"] = schedule_days
        self.data["schedule_time"] = schedule_time

        db.insert(g.cursor, "patterns", replace=True, id=self.id, **self.data)

    @classmethod
    def create(
        cls,
        pattern,
        name,
        user,
        host,
        recipients,
        schedule_days,
        schedule_time,
    ):
        db.insert(
            g.cursor,
            "patterns",
            pattern=pattern,
            name=name,
            user=user,
            host=host,
            recipients=recipients,
            schedule_days=schedule_days,
            schedule_time=schedule_time,
        )

        # instantiate self using last insert id
        return cls(g.cursor.lastrowid)

    def delete(self, user):
        # ensure only owners can delete patterns
        g.cursor.execute(
            """ DELETE FROM patterns
                WHERE id = %s
                AND user = %s""",
            (self.id, user),
        )
