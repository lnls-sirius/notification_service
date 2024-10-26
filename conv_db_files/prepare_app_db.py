""" Run this file to populate App.db with rules and admin user. """
import os, sqlite3

localdir = os.path.abspath(os.path.dirname(__file__))
basedir = os.path.abspath(os.path.join(localdir, os.pardir))
path_db = os.path.join(basedir, 'app/db/app.db')

def get_app_new_connection():
    # dir_path = os.path.dirname(os.path.realpath(__file__)) #current folder application path
    # db_path = os.path.join(dir_path, 'app.db')
    conn = sqlite3.connect(path_db)
    conn.row_factory = sqlite3.Row
    return conn

# ================ INSERT DATA IN RULES TABLE ================ #

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
        # print(id, rule, description)
        if rule_db is None:
            new_notifications.execute('INSERT INTO rules (id, rule, description) VALUES (?, ?, ?)', (id, rule, description))
            new_notifications.commit()
            print("Rule %s just inserted in database." % rule)
        else:
            print("!!! Rule %s already inserted in database !!!" % rule)

    # ================ INSERT ADMIN USER IN USERS TABLE ================ #

    id = 0
    username = "admin"
    email = "operacao.lnls@gmail.com"
    phone = "+5519996018157"
    waphone = phone
    ########### change password afterward, on the interface #############
    password_hash = "pbkdf2:sha256:150000$tmxKBtWX$4521c6377bb48426645f43931dc1748c42307e5ebdbe1cb4adaf8a4ba1986e97"

    user_admin = new_notifications.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone()
    if user_admin is None:
        new_notifications.execute('INSERT INTO users (id, username, email, phone, waphone, password_hash) VALUES (?, ?, ?, ?, ?, ?)', (id, username, email, phone, waphone, password_hash))
        new_notifications.commit()
        print("User admin added to users table.")
    else:
        print("User admin already in users table")
