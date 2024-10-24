from flask import Flask, url_for
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from iofunctions import fromcfg
from multiprocessing import Process

class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            #print(environ['PATH_INFO'])
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not exist in this application.".encode()]


app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)
login = LoginManager(app)
login.login_view = 'login'
p = fromcfg('PREFIX','prefix')
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=p)
# app.config['SESSION_PERMANENT'] = True
app.permanent_session_lifetime = 600

from app import routes, models
# bootstrap = Bootstrap(app)

with app.app_context():
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)

# run evaluate process to start backend
# if __name__ == "app":
#     from monitor import evaluate
#     p = Process(target=evaluate)
#     p.start()
#     print("\n\r")
