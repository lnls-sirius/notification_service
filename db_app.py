#!./venv/bin/python

import sqlite3, iofunctions, requests, urllib3
from os import path
from app.models import User, Notification, Rule
from app import db

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class App_db:
    def __init__(self, database):
        self.database = database

    def connect(self, db_name):
        current_folder = path.dirname(path.realpath(__file__))
        database_path = path.join(current_folder, "app/db/" + db_name)
        connection = sqlite3.connect(database_path)
        # connection.row_factory = sqlite3.Row
        return connection

    def get(self, field='all', value=None, rule_id=None, user_id=None, notification_id=None):
        result = 0
        databases = ["users", "notifications", "rules"]
        database = self.database
        if database not in databases:
            raise ValueError("Invalid model. Expected one of: %s" % databases)
        if database == "users":
            try:
                if field == "id":
                    result = db.session.query(User).filter_by(id=value).first()
                    #result = User.query.filter_by(id=value).first()
                    db.session.close()
                if field == "username":
                    result = db.session.query(User).filter_by(username=value).first()
                    db.session.close()
                    #result = User.query.filter_by(username=value).all()
                if field == "email":
                    result = db.session.query(User).filter_by(email=value).first()
                    db.session.close()
                    #result = User.query.filter_by(email=value).all()
                if field == "phone":
                    result = db.session.query(User).filter_by(phone=value).first()
                    db.session.close()
                    #result = User.query.filter_by(phone=value).first()
                if field == 'all':
                    result = db.session.query(User).all()
                    db.session.close()
                    #result = User.query.all()
            except Exception as e:
                result = e

        if database == "notifications":
            try:
                if field == "id":
                    result = db.session.query(Notification).filter_by(id=notification_id).first()
                    db.session.close()
                    #result = Notification.query.filter_by(id=value).first()
                if field == "user_id":
                    result = db.session.query(Notification).filter_by(user_id=user_id).first()
                    db.session.close()
                    #result = Notification.query.filter_by(user_id=value).all()
                if field == "all":
                    result = db.session.query(Notification).all()
                    # db.session.close()
                    #result = Notification.query.all()
            except Exception as e:
                print("Error on db_app.py, get function: ", e)
                result = e

        if database == "rules":
            try:
                if field == "all":
                    result = db.session.query(Rule).all()
                    db.session.close()
                    #result = Rule.query.all()
                if rule_id != None:
                    result = db.session.query(Rule).filter_by(id=value).first()
                    db.session.close()
                    #result = Rule.query.filter_by(id=rule_id).first()
            except Exception as e:
                result = e

        return result

    def add(self, field=None, user={}):
        if field == 'users':
            usr = User()
            usr.username = user["username"]
            usr.email = user["email"]
            usr.phone = user["phone"]
            usr.set_password(user["password"])
            db.session.add(usr)
            db.session.commit()

    def delete(self, field, id):
        if field == "users":
            User.query.filter_by(id=id).delete()
            # usr = db.session.query(User).filter_by(id=id).first()
            # db.session.delete(usr)
            db.session.commit()

    def update(self, id=None, key=None, value=None):
        ans = 0
        try:
            if self.database == "notifications":
                notification = db.session.query(Notification).filter_by(id=id).first()
                #notification = Notification.query.filter_by(id=id).first()
                if key == "notification":
                    notification.notification = value
                if key == "sms_text":
                    notification.sms_text = value
                if key == "last_sent":
                    notification.last_sent = value
                # db.session.query(Notification).filter_by(id=id).update({key: value})
                db.session.commit()
            if self.database == "users":
                user = db.session.query(User).filter_by(id=id).first()
                #user = User.query.filter_by(id=id).first()
                if key == "username":
                    user.username = value
                if key == "email":
                    user.email = value
                if key == "phone":
                    user.phone = value
                db.session.commit()
            if self.database == "rules":
                rule = db.session.query(Rule).filter_by(id=id).first()
                #rule = Rule.query.filter_by(id=id).first()
                rule.rule = value
                db.session.commit()
            ans = 1
        except Exception as e:
            print("Error on db_app.py, update function: ", e)
            ans = 0
            return ans
        return ans

    def close(self):
        db.session.close()

class FullPVList:
    def __init__(self):
        self.fullpvlist = []

    def __get_connection(self):
        database_path = iofunctions.fromcfg('FULLPVLIST', 'db')
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

    def is_pv_on_list(self, pv):
        if pv in self.fullpvlist:
            return True
        else:
            return False

    def update(self):
        try:
            current_folder = iofunctions.current_path()
            schema = iofunctions.fromcfg('FULLPVLIST', 'schema')
            schema_path = path.join(current_folder, schema)

            url = iofunctions.fromcfg('EPICS_SERVER','getallpvs')
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


# ls = datetime.strptime('2023-12-31 22:00', '%Y-%m-%d %H:%M')
# notification_db = App_db("rules")
# print(notification_db.get(rule_id=7))
# notification_db.update(id=7, value="(pv < LL) and (pv > LU)")
# print(notification_db.get(rule_id=7))
# print(notification_db.get(id, 28))
# users_db = App_db(users)
# print(users_db.get(id, 2))
# user_db = App_db(users)
# user_db.update(2, email, 'rone.castro@lnls.br')
# print(db.session.query(User).all())
# f = FullPVList()
# print(f.update())
