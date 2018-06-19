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

    @staticmethod
    def create(email, password):
        try:
            db.insert(
                g.cursor,
                "users",
                email=email,
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

    def update(self, **data):
        self.data.update(**data)
        db.update(g.cursor, "patterns", where={"id": self.id}, **self.data)

    @classmethod
    def create(cls, **data):
        db.insert(g.cursor, "patterns", **data)
        return cls(g.cursor.lastrowid)

    def delete(self, user):
        # ensure only owners can delete patterns
        db.delete(g.cursor, "patterns", id=self.id, user=user)
