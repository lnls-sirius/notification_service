import sqlite3, re, iofunctions, requests, json
from tkinter import E
from app.models import Notification, User, Rule
from app import db
from os import path, getcwd
from flask import jsonify
from time import sleep

def get_connection(database):
    current_folder = path.dirname(path.realpath(__file__))
    database_path = path.join(current_folder, database)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def update_fullpvlist():
    dir_path = path.dirname(path.realpath(__file__)) #current folder application path
    schema_path = 'app/db/schema_fullpvlist.sql'
    fullpvlist_path = 'app/db/fullpvlist.db'
    db_path = path.join(dir_path, fullpvlist_path)
    connection = sqlite3.connect(db_path)

    sql_path = path.join(dir_path, schema_path)
    with open(sql_path) as f:
        connection.executescript(f.read())

    cur = connection.cursor()

    epics_server = iofunctions.fromcfg('EPICS_SERVER','ip')
    prefix = iofunctions.fromcfg('GET_ALL_PVS','prefix')
    suffix = iofunctions.fromcfg('GET_ALL_PVS','suffix')
    url = prefix + epics_server + suffix

    r = requests.get(url, allow_redirects=True, verify=False)
    fullpvlist = r.text.replace('"','').replace('[','').replace(']','').split(',')

    for pv in fullpvlist:
        cur.execute("INSERT INTO fullpvlist_db (pv) VALUES (?)", (pv,))
    connection.commit()
    connection.close()

    return 'ok'


def pvlistfromdb(): # gets the list from fullpvlist.db
    dir_path = path.dirname(path.realpath(__file__))
    fullpvlist_path = 'app/db/fullpvlist.db'
    db_path = path.join(dir_path, fullpvlist_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn_fullpvlist = conn
    fullpvlist = conn_fullpvlist.execute('SELECT pv FROM fullpvlist_db').fetchall()
    m = []
    for row in fullpvlist:
        for i in row:
            m.append(i)
    return m

def searchdb(search, inroute=False):
    def regexp(expr, item):
        reg = re.compile(expr)
        return reg.search(item) is not None
    dir_path = path.dirname(path.realpath(__file__))
    dir_path = getcwd()
    fullpvlist_path = 'app/db/fullpvlist.db'
    db_path = path.join(dir_path, fullpvlist_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.create_function("REGEXP", 2, regexp)
    search_plus = "^" + search + "$"
    results = conn.execute('SELECT * FROM fullpvlist_db WHERE pv REGEXP ? LIMIT 10',(search_plus,))
    m = []
    for row in results:
        for i in row:
            m.append(i)
    result = jsonify(matching_results=m)
    if inroute == True:
        return m
    return result


def update_db(database, id, key=None, value=None):
    try:
        if database == 'Notification':
            db.session.query(Notification).filter_by(id=id).update({key: value})
            db.session.commit()
        if database == 'User':
            db.session.query(User).filter_by(id=id).update({key: value})
            db.session.commit()
        if database == 'Rule':
            db.session.query(Rule).filter_by(id=id).update({key: value})
            db.session.commit()
        ans = 'ok'
    except Exception as e:
        return e
    return ans
