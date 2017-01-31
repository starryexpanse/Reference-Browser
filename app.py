from flask import Flask

def create_app():
  app = Flask(__name__)
  app.config.from_pyfile('config.py')
  app.config.from_pyfile('instance/config.py')

  from browser.models import db, test_password
  db.init_app(app)
  with open('instance/password.txt', 'r') as f:
    test_password = f.readline()

  from browser.views import browsing, login_manager
  app.register_blueprint(browsing)
  login_manager.init_app(app)

  return app

if __name__ == '__main__':
  browser = create_app()
  browser.run()
