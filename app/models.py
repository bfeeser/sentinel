"""
Ben Feeser
Sentinel

Library of class models.
"""

from app import bcrypt, cursor, db
from flask_login import UserMixin


# define user class per flask-login spec
# https://flask-login.readthedocs.org/en/latest/
class User(UserMixin):

    def __init__(self, email):
        # define user values upon init; set to empty
        self.data = {}
        self.email = email
        self.id = None

        # get user attributes from database
        cursor.execute(
            """ SELECT *
                FROM users
                WHERE email = %s""",
            (email,),
        )

        if cursor.rowcount:
            # store attributes in a dictionary
            cols = [i[0] for i in cursor.description]
            self.data = dict(zip(cols, cursor.fetchone()))

            # flask-login only accepts unicode ids
            self.id = str(self.data["id"])

    def add(self, password):
        # method to add user into db
        # returns false on failure; true on success
        try:
            cursor.execute(
                """ INSERT INTO users
                        (email, password)
                    VALUES(%s, %s)
                """,
                (self.email, bcrypt.generate_password_hash(password)),
            )
        except Exception as e:
            # insert was unsuccessful
            print(e)
            return False
        else:
            # insert was successful
            db.commit()
            return True


class Pattern(object):
    # defines a pattern object
    # contains helper methods for retrieving assoc data

    def __init__(self, id):
        # define pattern values upon init; set to empty
        self.data = {}
        self.id = id

        # get pattern attributes from database
        cursor.execute(
            """ SELECT *
                FROM patterns
                WHERE id = %s""",
            (id,),
        )

        if cursor.rowcount:
            # store attributes in a dictionary
            cols = [i[0] for i in cursor.description]
            self.data = dict(zip(cols, cursor.fetchone()))

            # set schedule time to string; not a time object
            if self.data["schedule_time"]:
                self.data["schedule_time"] = str(self.data["schedule_time"])

    def get_host(self):
        # using pattern host id get host info
        cursor.execute(
            """ SELECT host, host_user, path
                FROM hosts
                WHERE id = %s""",
            (self.data.get("host"),),
        )

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

        # build query to update db
        cursor.execute(
            """ REPLACE INTO patterns
                (id, pattern, name, user, host, recipients,
                 schedule_days, schedule_time)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                self.id,
                pattern,
                name,
                user,
                host,
                recipients,
                schedule_days,
                schedule_time,
            ),
        )

        db.commit()

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
        # function to create pattern
        # build query to insert into db
        cursor.execute(
            """ INSERT INTO patterns
                (pattern, name, user, host, recipients,
                 schedule_days, schedule_time)
                VALUES(%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pattern,
                name,
                user,
                host,
                recipients,
                schedule_days,
                schedule_time,
            ),
        )

        db.commit()

        # instantiate self using last insert id
        return cls(cursor.lastrowid)

    def delete(self, user):
        # ensure only owners can delete patterns
        cursor.execute(
            """ DELETE FROM patterns
                WHERE id = %s
                AND user = %s""",
            (self.id, user),
        )

        db.commit()
