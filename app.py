from flask import Flask
import os

def create_app():
  dirpath = os.path.dirname(os.path.abspath(__file__))

  app = Flask(__name__)
  app.config.from_pyfile(os.path.join(dirpath, 'config.py'))
  app.config.from_pyfile(os.path.join(dirpath, 'instance', 'config.py'))

  from browser.models import db, SetTestPassword
  db.init_app(app)
  with open(os.path.join(dirpath, 'instance', 'password.txt'), 'r') as f:
    SetTestPassword(f.readline().strip())

  from browser.views import browsing, login_manager
  app.register_blueprint(browsing)
  login_manager.init_app(app)

  return app

if __name__ == '__main__':
  browser = create_app()
  browser.run()
