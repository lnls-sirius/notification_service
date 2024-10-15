#!./venv/bin/python
"""This script is used for database migration from the older version of SMS Service to the new Notification Service format. Before, we used to have three separate files, each with a table: 'notifications.db' for the notifications, 'users.db' for user names and 'rules.db' for rules with descriptions. Now all tables are in a single file, app.db."""
import os, sys, sqlite3, re
from datetime import datetime as dt
from json import dumps
from prepare_app_db import prepare_app_db

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
upper_parent_dir_path = os.path.abspath(os.path.join(parent_dir_path, os.pardir))
sys.path.insert(0, upper_parent_dir_path)

# from db import App_db, User

def get_app_new_connection():
    dir_path = os.path.dirname(os.path.realpath(__file__)) #current folder application path
    db_path = os.path.join(dir_path, 'app.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_notifications_old_connection():
    dir_path = os.path.dirname(os.path.realpath(__file__)) #current folder application path
    # print(dir_path)
    db_path = os.path.join(dir_path, 'notifications.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_users_old_connection():
    dir_path = os.path.dirname(os.path.realpath(__file__)) #current folder application path
    # print(dir_path)
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

# ADD ADMIN USER AND RULES DATA
prepare_app_db()

old_db_name = 'notifications.db'
current_folder = os.path.dirname(os.path.realpath(__file__))
database_path_old = os.path.join(current_folder, old_db_name)
# print("database_path_old", database_path_old)
# sql_query_table = """SELECT name FROM sqlite_master
#   WHERE type='table';"""
sql_query_rows_old  = """SELECT * FROM notifications_db"""
conn_old = sqlite3.connect(database_path_old)
cursor_old = conn_old.cursor()
# cursor.execute(sql_query_table)
cursor_old.execute(sql_query_rows_old)
# print("tables", cursor.fetchall())
rows = cursor_old.fetchall()
names = list(map(lambda x: x[0], cursor_old.description))
# print(type(names))
# for name in names:
#     print(name)
# for row in rows:
#     print(row)
# conn_old.row_factory = sqlite3.Row
# rows_old_notifications = conn_old.execute("SELECT * FROM notifications_db").fetchall()

# ============= OLD USERS CONNECTION =============
old_users = get_users_old_connection() # 'users.db'

# ============= OLD NOTIFICATION CONNECTION =============
old_notifications = get_notifications_old_connection() # 'notifications.db'

# ============= NEW NOTIFICATION CONNECTION =============
new_notifications = get_app_new_connection() #'app.db'
# rows_new_notifications = new_notifications.execute("SELECT * FROM notifications").fetchall()

# sql_query_rows_new  = """SELECT * FROM notifications"""
# cursor_new = new_notifications.cursor()
# cursor_new.execute(sql_query_rows_new)
# print("notifications", cursor_new.fetchall())
# rows = cursor_new.fetchall()
# names = list(map(lambda x: x[0], cursor_new.description))
# i = 0
# for row in rows:
#     for col in row:
#         print(names[i]+ ":", col)
#         i += 1

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
        # username_str = list(row_username)[0]
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
        # print('owner:', user_db_username)
        user_db_phone = new_notifications.execute("SELECT phone FROM users WHERE username=?", (owner,)).fetchone()[0]
        # print("owner", user_db_username[0], "phone", user_db_phone)
        if user_db_username is not None:
            if user_db_phone == '':
                new_notifications.execute('UPDATE users SET phone=? WHERE username=?', (phone, owner))
                new_notifications.execute('UPDATE users SET waphone=? WHERE username=?', (phone, owner))
                new_notifications.commit()
                print("Phone/Whatsapp %s added for user %s" % (phone, owner))
            else:
                print("User %s already have a phone number set." % owner)

    nc = []

    if limits1 != '':
        limits1 = limits1.split("L=")[1]
    core0 = {"notificationCore0": {"pv0": pv1, "rule0": rule1, "limit0": limits1, "subrule0": subrule1.upper()}}

    nc.append(core0)

    if subrule1 != '':
        if limits2 != '':
            limits2 = limits2.split("L=")[1]
        core1 = {"notificationCore1": {"pv1": pv2, "rule1": rule2, "limit1": limits2, "subrule1": subrule2.upper()}}
        nc.append(core1)

    id = i

    user_id = new_notifications.execute("SELECT id FROM users WHERE username=?", (owner,)).fetchone()
    user_id = user_id[0]

    notification = {"created": created, "expiration": expiration, "interval": interval, "persistence": persistent, "notificationCores": nc}
    notification = dumps(notification)

    last_sent = dt.strptime(sent_time, '%Y-%m-%d %H:%M:%S.%f')

    sms_text = ''

    # print(id, user_id, notification, last_sent, sms_text)
    # print(type(id), type(user_id), type(notification), type(last_sent), type(sms_text))
    # print(" ")

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
