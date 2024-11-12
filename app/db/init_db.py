#!./venv/bin/python
"""This script is used for database initialization. It creates 
the app.db file with tables, insert the admin user and rules. 
Also creates 'migrations' folder."""
import os, sqlite3
from time import sleep
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import subprocess
import shutil
import configparser
import requests
import urllib3

urllib3.disable_warnings()

localdir = os.path.abspath(os.path.dirname(__file__))
appdir = os.path.abspath(os.path.join(localdir, os.pardir))
basedir = os.path.abspath(os.path.join(appdir, os.pardir))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'db/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)
db.engine.url.drivername == 'sqlite'
migrate = Migrate(app, db)
migrate_dir = 'migrations'
path_m = os.path.join(basedir, 'migrations')
path_db = os.path.join(basedir, 'app/db/app.db')


def get_app_new_connection():
    conn = sqlite3.connect(path_db)
    conn.row_factory = sqlite3.Row
    return conn

def prepare_app_db():
    new_notifications = get_app_new_connection()

    rules =  {0 : ["pv == L", "PV value is equal to Limit"],
            1 : ["pv != L", "PV value is different from Limit"],
            2 : ["pv > L", "PV value is greater than Limit"],
            3 : ["pv < L", "PV value is less than Limit"],
            4 : ["pv >= L", "PV value is greater than or equal to Limit"],
            5 : ["pv <= L", "PV value is less than or equal to Limit"],
            6 : ["(pv < LL) or (pv > LU)", "PV value is outside range"],
            7 : ["(pv > LL) and (pv < LU)", "PV value is within range"]}

    for key in rules:
        id = key
        rule = rules[key][0]
        description = rules[key][1]
        rule_db = new_notifications.execute("SELECT rule FROM rules WHERE rule=?", (rule,)).fetchone()

        if rule_db is None:
            new_notifications.execute('INSERT INTO rules (id, rule, description) VALUES (?, ?, ?)', (id, rule, description))
            new_notifications.commit()
            print("Rule %s just inserted in database." % rule)
        else:
            print("!!! Rule %s already inserted in database !!!" % rule)

    id = 0
    username = "admin"
    email = "operacao.lnls@gmail.com"
    phone = "+5519996018157"
    waphone = phone
    password_hash = "pbkdf2:sha256:150000$tmxKBtWX$4521c6377bb48426645f43931dc1748c42307e5ebdbe1cb4adaf8a4ba1986e97"

    user_admin = new_notifications.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone()
    if user_admin is None:
        new_notifications.execute('INSERT INTO users (id, username, email, phone, waphone, password_hash) VALUES (?, ?, ?, ?, ?, ?)', (id, username, email, phone, waphone, password_hash))
        new_notifications.commit()
        print("User admin added to users table.")
    else:
        print("User admin already in users table")

def current_path(file=None):
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__), )
        if file != None:
            config_path = os.path.join(dir_path, file)
            return config_path
        else:
            return dir_path
    except Exception as e:
        return e
    
def fromcfg(section,key):
    try:
        fullpath = os.path.join(basedir, "config.cfg")
        config = configparser.RawConfigParser()
        config.read_file(open(fullpath))
        r = config.get(section,key)
    except:
        print("Error on reading 'config.cfg' file")
        return None
    return r

class fpvlist():
    def __init__(self):
        self.fullpvlist = []
    
    def __get_connection(self):
        database_path = fromcfg('FULLPVLIST', 'db')
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def update(self):
        try:
            schema_path = os.path.join(localdir, "fullpvlist.sql")

            url = fromcfg('EPICS_SERVER','getallpvs')
            r = requests.get(url, allow_redirects=True, verify=False, timeout=5)

            if r.status_code == 503:
                raise Exception('Error, could not get PVs from server.')

            else:
                connection = self.__get_connection()

                with open(schema_path) as f:
                    connection.executescript(f.read())

                cur = connection.cursor()

                fullpvlist = r.text.replace('"','').replace('[','').replace(']','').split(',')

                for pv in fullpvlist:
                    cur.execute("INSERT INTO fullpvlist_db (pv) VALUES (?)", (pv,))
                connection.commit()
                connection.close()
        except Exception as e:
            return e

    def getlist(self):
        connection = self.__get_connection()
        db = connection.execute('SELECT pv FROM fullpvlist_db').fetchall()
        for row in db:
            for i in row:
                self.fullpvlist.append(i)
        return self.fullpvlist

def prepare_fullpvlist_db():
    try:
        f = fpvlist()
        f.update()
        f.getlist()
        print("Full PV List created")
    except Exception as e:
        print("Error on prepare_evaluate function: ", e)
        exit()


with app.app_context():
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)
    
    ok_sig = False

    if not os.path.exists(path_m):
        try:
            subprocess.run(["flask", "db", "init"])
            sleep(5)
            subprocess.run(["flask", "db", "migrate", "-m", "'app.db'"])
            sleep(5)
            subprocess.run(["flask", "db", "upgrade"])
            sleep(5)
            ok_sig = True
        except Exception as e:
            print("Error on create app.db and migration.")
            exit()
        if ok_sig:
            # ADD ADMIN USER AND RULES DATA
            prepare_app_db()
            print("app.db prepared!")
            prepare_fullpvlist_db()
    else:
        try:
            os.remove(path_db)
        except FileNotFoundError:
            print("Could not remove app.db")
        shutil.rmtree(path_m, ignore_errors=True)
        ok_sig = False
        try:
            subprocess.run(["flask", "db", "init"])
            sleep(5)
            subprocess.run(["flask", "db", "migrate", "-m", "'app.db'"])
            sleep(5)
            subprocess.run(["flask", "db", "upgrade"])
            sleep(5)
            ok_sig = True
        except Exception as e:
            print("Error on create app.db and migration.")
            exit()
        if ok_sig:
            # ADD ADMIN USER AND RULES DATA
            prepare_app_db()
            print("app.db prepared!")
            prepare_fullpvlist_db()

