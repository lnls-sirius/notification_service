#!./venv/bin/python
"""This script is used for database migration from the older 
version of SMS Service to the new Notification Service format. 
Before, we used to have three separate files, each with a 
table: 'notifications.db' for the notifications, 'users.db' 
for user names and 'rules.db' for rules with descriptions. 
Now all tables are in a single file, app.db."""
import os, sys, sqlite3, re, configparser
from datetime import datetime as dt
from json import dumps
from time import sleep
from flask import Flask
from flask_migrate import Migrate, init, upgrade
from flask_sqlalchemy import SQLAlchemy
import subprocess
import shutil
from epics import PV

localdir = os.path.abspath(os.path.dirname(__file__))
basedir = os.path.abspath(os.path.join(localdir, os.pardir))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app/db/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)
db.engine.url.drivername == 'sqlite'
migrate = Migrate(app, db)
migrate_dir = 'migrations'
path_m = os.path.join(basedir, 'migrations')
path_db = os.path.join(basedir, 'app/db/app.db')


def current_path(file=None):
    try:
        localdir = os.path.abspath(os.path.dirname(__file__))
        basedir = os.path.abspath(os.path.join(localdir, os.pardir))
        if file != None:
            config_path = os.path.join(basedir, file)
            return config_path
        else:
            return dir_path
    except Exception as e:
        return e

def fromcfg(section,key):
    try:
        fullpath = current_path('config.cfg')
        config = configparser.RawConfigParser()
        config.read_file(open(fullpath))
        r = config.get(section,key)
    except:
        print("Error on reading 'config.cfg' file")
        return None
    return r

class FullPVList:
    def __init__(self):
        self.fullpvlist = []

    def __get_connection(self):
        database_path = fromcfg('FULLPVLIST', 'db')
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def getlist(self):
        connection = self.__get_connection()
        db = connection.execute('SELECT pv FROM fullpvlist_db').fetchall()
        for row in db:
            for i in row:
                self.fullpvlist.append(i)
        return self.fullpvlist


f = FullPVList()
fullpvlist = f.getlist()

def get_app_new_connection():
    conn = sqlite3.connect(path_db)
    conn.row_factory = sqlite3.Row
    return conn

def get_notifications_old_connection():
    dir_path = os.path.dirname(os.path.realpath(__file__)) #current folder application path
    db_path = os.path.join(dir_path, 'notifications.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_users_old_connection():
    dir_path = os.path.dirname(os.path.realpath(__file__)) #current folder application path
    db_path = os.path.join(dir_path, 'users.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    return dict(zip(row.keys(), row))

def format_phone(phone):
    phone = re.sub('\D', '', phone)
    if phone[0:2] != '+55':
        phone = '+55' + phone
    return phone

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

def checkPV(pvname):
    pvlist = []
    comp_regex = re.compile(pvname)
    filterlist = list(filter(comp_regex.match, fullpvlist))
    for item in filterlist:
        if item not in pvlist:
            pvlist.append(item)
    for pvname_ in pvlist:
        pv_ = PV(pvname_)
        if not pv_.connected:
            print("pv %s not connected!" % pv_.pvname)
        else:
            print("pv %s value:" % pv_.pvname, pv_.value)


with app.app_context():
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)

    if not os.path.exists('migrations'):
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
 

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
upper_parent_dir_path = os.path.abspath(os.path.join(parent_dir_path, os.pardir))
sys.path.insert(0, upper_parent_dir_path)


def main():
    old_db_name = 'notifications.db'
    current_folder = os.path.dirname(os.path.realpath(__file__))
    database_path_old = os.path.join(current_folder, old_db_name)
    sql_query_rows_old  = """SELECT * FROM notifications_db"""
    conn_old = sqlite3.connect(database_path_old)
    cursor_old = conn_old.cursor()
    cursor_old.execute(sql_query_rows_old)

    # ============= OLD USERS CONNECTION =============
    old_users = get_users_old_connection() # 'users.db'

    # ============= OLD NOTIFICATION CONNECTION =============
    old_notifications = get_notifications_old_connection() # 'notifications.db'

    # ============= NEW NOTIFICATION CONNECTION =============
    new_notifications = get_app_new_connection() #'app.db'

    #============= NEW DB ==============#
    id = ''
    user_id = ''
    notification = ''
    last_sent = ''
    sms_text = ''

    #============= OLD DB ==============#
    id = ''
    created = ''
    expiration = ''
    pv1 = ''
    rule1 = ''
    limits1 = ''
    subrule1 = ''
    pv2 = ''
    rule2 = ''
    limits2 = ''
    subrule2 = ''
    pv3 = ''
    rule3 = ''
    limits3 = ''
    subrule3 = ''
    owner = ''
    phone = ''
    sent = ''
    sent_time = ''
    interval = ''
    persistent = ''

    i=0
    j=0
    k=0

    user_id = ''
    username = ''
    email = ''
    phone = ''
    waphone = ''
    password_hash = ''
    rows_old_users = old_users.execute("SELECT * FROM user").fetchall()
    users = []

    for row in rows_old_users:
        j = 0
        for row in rows_old_users[i]:
            if j==0:
                user_id = rows_old_users[i][j]
            if j==1:
                username = rows_old_users[i][j]
            if j==2:
                password_hash = rows_old_users[i][j]
            j += 1
        i += 1

        # print("=================== - row %i done" % i, "======================")
        # print('user_id: ', (user_id))
        # print('username: ', (username))
        # print('password_hash: ', (password_hash))
        # print('email: ', (email))
        # print('phone: ', phone)
        # print('waphone: ', waphone)

        id = k #user_id
        email = username + "@lnls.br"
        phone = ''
        waphone = phone
        exclude = ['carlos.vieira', 'operador', 'rcardoso', 'rafael', 'maria.gardingo', 'wagnerbento', 'wagner_bento', 'wagner.bento', 'rafael.cardoso']
        row_username = new_notifications.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone()

        if row_username is None:
            if username not in exclude:
                new_notifications.execute('INSERT INTO users (id, username, email, phone, waphone, password_hash) VALUES (?, ?, ?, ?, ?, ?)',
                (id, username, email, phone, waphone, password_hash))
                new_notifications.commit()
                k += 1
                print('New database entry included for user %s' % username)
                users.append(username)
        else:
            print("User %s already included in dabatase." % username)
            k += 1
            users.append(username)

    i=0
    j=0
    k=0
    rows_old_notifications = old_notifications.execute("SELECT * FROM notifications_db").fetchall()

    for row in rows_old_notifications:
        j = 0
        for row in rows_old_notifications[i]:
            if j==0:
                id = rows_old_notifications[i][j]
            if j==1:
                created = rows_old_notifications[i][j]
            if j==2:
                expiration = rows_old_notifications[i][j]
            if j==3:
                owner = rows_old_notifications[i][j]
            if j==4:
                phone = rows_old_notifications[i][j]
            if j==5:
                pv1 = rows_old_notifications[i][j]
            if j==6:
                rule1 = rows_old_notifications[i][j]
            if j==7:
                limits1 = rows_old_notifications[i][j]
            if j==8:
                subrule1 = rows_old_notifications[i][j]
            if j==9:
                pv2 = rows_old_notifications[i][j]
            if j==10:
                rule2 = rows_old_notifications[i][j]
            if j==11:
                limits2 = rows_old_notifications[i][j]
            if j==12:
                subrule2 = rows_old_notifications[i][j]
            if j==13:
                pv3 = rows_old_notifications[i][j]
            if j==14:
                rule3 = rows_old_notifications[i][j]
            if j==15:
                limits3 = rows_old_notifications[i][j]
            if j==16:
                sent = rows_old_notifications[i][j]
            if j==17:
                sent_time = rows_old_notifications[i][j]
            if j==18:
                interval = str(rows_old_notifications[i][j])
            if j==19:
                persistent = 'YES' if rows_old_notifications[i][j] == 1 else 'NO'
            j += 1

        # checkPV(pv1)
        # checkPV(pv2)

        # print("=================== - row %i done" % i, "======================")
        # print('id: ', (id))
        # print('created: ', (created))
        # print('expiration: ', (expiration))
        # print('pv1: ', (pv1))
        # print('rule1: ', (rule1))
        # print('limits1: ', (limits1))
        # print('subrule1: ', (subrule1))
        # print('pv2: ', (pv2))
        # print('rule2: ', (rule2))
        # print('limits2: ', (limits2))
        # print('subrule2: ', (subrule2))
        # print('owner: ', (owner))
        # print('phone: ', (phone))
        # print('sent: ', (sent))
        # print('sent_time: ', (sent_time))
        # print('interval: ', (interval))
        # print('persistent: ', (persistent))

        if owner in users:
            users.remove(owner)
            phone = format_phone(phone)
            user_db_username = new_notifications.execute("SELECT username FROM users WHERE username=?", (owner,)).fetchone()
            user_db_phone = new_notifications.execute("SELECT phone FROM users WHERE username=?", (owner,)).fetchone()[0]
            if user_db_username is not None:
                if user_db_phone == '':
                    new_notifications.execute('UPDATE users SET phone=? WHERE username=?', (phone, owner))
                    new_notifications.execute('UPDATE users SET waphone=? WHERE username=?', (phone, owner))
                    new_notifications.commit()
                    print("Phone/Whatsapp %s added for user %s" % (phone, owner))
                else:
                    print("User %s already have a phone number set." % owner)

        nc = []

        if "LL" in rule1:
            limitLL0 = limits1.split("LL=")[1].split(";LU=")[0]
            limitLU0 = limits1.split("LU=")[1]
            core0 = {"notificationCore0": {"pv0": pv1,
                                    "rule0": rule1,
                                    "limitLL0": limitLL0,
                                    "limitLU0": limitLU0,
                                    "subrule0": subrule1.upper()}}

        else:
            if limits1 != '':
                limits1 = limits1.split("L=")[1]
                core0 = {"notificationCore0": {"pv0": pv1,
                                            "rule0": rule1,
                                            "limit0": limits1,
                                            "subrule0": subrule1.upper()}}

        nc.append(core0)

        if "LL" in rule2:
            limitLL1 = limits2.split("LL=")[1].split(";LU=")[0]
            limitLU1 = limits2.split("LU=")[1]
            core1 = {"notificationCore1": {"pv1": pv2,
                                        "rule1": rule2,
                                        "limitLL1": limitLL1,
                                        "limitLU1": limitLU1,
                                        "subrule1": subrule2.upper()}}
        else:
            if subrule1 != '':
                if limits2 != '':
                    limits2 = limits2.split("L=")[1]
                    core1 = {"notificationCore1": {"pv1": pv2,
                                                "rule1": rule2,
                                                "limit1": limits2,
                                                "subrule1": subrule2.upper()}}
                nc.append(core1)

        id = i

        user_id = new_notifications.execute("SELECT id FROM users WHERE username=?", (owner,)).fetchone()
        user_id = user_id[0]
        
        sms_text = ''

        created = dt.strptime(created, '%Y-%m-%d %H:%M:%S')
        created = created.strftime('%Y-%m-%d %H:%M')

        expiration = dt.strptime(expiration, '%Y-%m-%d %H:%M:%S')
        expiration = expiration.strftime('%Y-%m-%d %H:%M')
        notification = {"created": created, "expiration": expiration, "interval": interval, "persistence": persistent, "notificationCores": nc}
        notification = dumps(notification)

        last_sent = dt.strptime(sent_time, '%Y-%m-%d %H:%M:%S.%f')

        new_notifications.execute('INSERT INTO notifications (id, user_id, notification, last_sent, sms_text) VALUES (?, ?, ?, ?, ?)', (id, user_id, notification, last_sent, sms_text))
        new_notifications.commit()

        id = ''
        created = ''
        expiration = ''
        pv1 = ''
        rule1 = ''
        limits1 = ''
        subrule1 = ''
        pv2 = ''
        rule2 = ''
        limits2 = ''
        subrule2 = ''
        pv3 = ''
        rule3 = ''
        limits3 = ''
        subrule3 = ''
        owner = ''
        phone = ''
        sent = ''
        sent_time = ''
        interval = ''
        persistent = ''

        i += 1

main()