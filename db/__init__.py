from configparser import ConfigParser
from collections import OrderedDict
import os
import pymysql


def read_config(path="db/config"):
    if os.path.exists("db/config"):
        config = ConfigParser()
        config.read(path)
        return config
    else:
        raise RuntimeError(f"Missing {path} config file")


def connect(**kwargs):
    config = read_config()

    params = {}
    params["charset"] = "utf8"
    params["connect_timeout"] = 10
    params["local_infile"] = 1
    params["db"] = "sentinel"  # TODO: unhardcode
    params["host"] = config.get("client", "host")
    params["user"] = config.get("client", "user")
    params["password"] = config.get("client", "password")
    params.update(**kwargs)

    db = pymysql.connect(**params)

    return db, db.cursor()


def _as_dict(keys, values, ordered=False):
    items = dict(zip(keys, values))
    return OrderedDict(items) if ordered else dict(items)


def result_as_dict(cursor, ordered=False):
    cols = [c[0] for c in cursor.description]
    return _as_dict(cols, cursor.fetchone(), ordered=ordered)


def result_as_list(cursor, ordered=False):
    cols = [c[0] for c in cursor.description]
    return [_as_dict(cols, row, ordered=ordered) for row in cursor.fetchall()]


def query(cursor, table, select="*", **where):
    cursor.execute(
        f"""
        SELECT {select}
        FROM {table}
        {build_where(*where.keys())}
        """,
        tuple(where.values()),
    )


def build_where(*columns):
    return f"WHERE {build_clause(*columns) or 1}"


def build_clause(*columns):
    if not columns:
        return ""

    ret = ""
    for i, column in enumerate(columns):
        if i > 0:
            ret += "    "
        ret += f"{column} = %s\n"

    return ret


def insert(cursor, table, replace=False, **data):
    if not data:
        raise ValueError("data argument is required")

    cursor.execute(
        f"""
        {'REPLACE' if replace else 'INSERT'} INTO {table}
            ({', '.join(data.keys())})
        VALUES ({', '.join('%s' for k in data)})
        """,
        tuple(data.values()),
    )


def update(cursor, table, where={}, **data):
    if not data:
        raise ValueError("data argument is required")

    cursor.execute(
        f"""
        UPDATE {table}
        SET {build_clause(*data.keys())}
        {build_where(*where.keys())}
        """,
        tuple(data.values()) + tuple(where.values()),
    )


def delete(cursor, table, **where):
    cursor.execute(
        f"""
        DELETE FROM {table}
        {build_where(*where.keys())}
        """,
        tuple(where.values()),
    )
