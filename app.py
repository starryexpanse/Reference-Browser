from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, \
    send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required,\
     current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from urlparse import urlparse, urljoin
from wtforms import validators, StringField, PasswordField
import json
import os

# Load app configuration data
path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
with open(os.path.join(dir_path, 'config.json')) as data_file:
  config = json.load(data_file)

app = Flask(__name__, static_url_path = "/static", static_folder = "static")
app.config['SQLALCHEMY_DATABASE_URI'] = config['db_url']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
#app.config['SQLALCHEMY_ECHO'] = True
# From random.org
app.config['SECRET_KEY'] = config['secret']
db = SQLAlchemy(app)
db.session.commit()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(db.Model, UserMixin):
  __tablename__ = 'users'
  id = db.Column('user_id', db.Integer, primary_key = True)
  username = db.Column(db.String(100))
  name = db.Column(db.String(100))

  def __init__(self):
    self.authenticated = False

  def get_id(self):
    return self.id

  def check_password(self, password):
    return password == config['test_pwd']

class Island(db.Model):
  __tablename__ = 'islands'
  id = db.Column('island_id', db.Integer, primary_key = True)
  symbol = db.Column(db.String(2))
  name = db.Column(db.String(100))
  aka = db.Column(db.String(200))
  suffix = db.Column(db.String(200))
  icon = db.Column(db.String(256))

  def title(self):
    t = '(%s) %s' % (self.symbol, self.name)
    if self.aka:
      t = '%s (AKA %s)' % (t, self.aka)
    if self.suffix:
      t += ' ' + self.suffix
    return t

class Position(db.Model):
  __tablename__ = 'positions'
  id = db.Column('position_id', db.Integer, primary_key = True)
  thumbnail = db.Column(db.String(256))
  island = db.Column('island', db.ForeignKey('islands.island_id'),
                     nullable=False)

class Viewpoint(db.Model):
  __tablename__ = 'viewpoints'
  id = db.Column('viewpoint_id', db.Integer, primary_key = True)
  island = db.Column('island', db.ForeignKey('islands.island_id'),
                     nullable=False)
  position = db.Column('position', db.ForeignKey('positions.position_id'),
                     nullable=True)
  name = db.Column(db.String(100))
  thumbnail = db.Column(db.String(256))
  thumbnail2x = db.Column(db.String(256))

class RivenImage(db.Model):
  __tablename__ = 'rivenimgs'
  id = db.Column('image_id', db.Integer, primary_key = True)
  viewpoint = db.Column('viewpoint', db.ForeignKey('viewpoints.viewpoint_id'),
                        nullable=False)
  filename = db.Column(db.String(100))
  friendly = db.Column(db.String(100))
  file_path = db.Column(db.String(256))

class RivenMovie(db.Model):
  __tablename__ = 'rivenmovs'
  id = db.Column('movie_id', db.Integer, primary_key = True)
  viewpoint = db.Column('viewpoint', db.ForeignKey('viewpoints.viewpoint_id'),
                        nullable=False)
  filename = db.Column(db.String(100))
  friendly = db.Column(db.String(100))
  file_path = db.Column(db.String(256))
  anim_gif_path = db.Column(db.String(256))
  h264_path = db.Column(db.String(256))

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

def is_safe_url(target):
  ref_url = urlparse(request.host_url)
  test_url = urlparse(urljoin(request.host_url, target))
  return test_url.scheme in ('http', 'https') and \
         ref_url.netloc == test_url.netloc

class LoginForm(FlaskForm):
  username = StringField('Username', [validators.DataRequired()])
  password = PasswordField('Password', [validators.DataRequired()])

  def __init__(self, *args, **kwargs):
    # Temporary - can't figure out why CSRF isn't working
    FlaskForm.__init__(self, *args, **kwargs)
    self.user = None

  def validate(self):
    if not FlaskForm.validate(self):
      return False

    user = User.query.filter_by(username=self.username.data).first()
    if user is None:
      self.username.errors.append('Unknown username')
      return False

    if not user.check_password(self.password.data):
      self.password.errors.append('Invalid password')
      return False

    self.user = user
    return True

@app.route('/')
@login_required
def islands():
  query = Island.query.order_by(Island.symbol).all()
  return render_template('islands.html', islands=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
  # Here we use a class of some kind to represent and validate our
  # client-side form data. For example, WTForms is a library that will
  # handle this for us, and we use a custom LoginForm to validate.
  form = LoginForm()
  if form.validate_on_submit():
    # Login and validate the user.
    # user should be an instance of your `User` class
    login_user(form.user)

    flash('Logged in successfully.')

    next = request.args.get('next')
    # is_safe_url should check if the url is safe for redirects.
    # See http://flask.pocoo.org/snippets/62/ for an example.
    if not is_safe_url(next):
      return app.abort(400)

    return redirect(next or url_for('islands'))
  return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for('islands'))

@app.route('/island/<symbol>')
@login_required
def island(symbol):
  island = Island.query.filter(Island.symbol == symbol).first()
  if not island:
    return 'There is no "%s" island.' % symbol

  vpt_name = request.args.get('viewpoint', '')
  if vpt_name:
    vpt_query = Viewpoint.query.filter(
        Viewpoint.island == island.id, Viewpoint.name == vpt_name)
    viewpoint = vpt_query.first()
    if not viewpoint:
      return 'There is no "%s" viewpoint.' % vpt_name
    title = '%s Viewpoint %s' % (island.title(), viewpoint.name)
    img_query=RivenImage.query.filter(
        RivenImage.viewpoint == viewpoint.id).order_by(RivenImage.friendly)
    mov_query=RivenMovie.query.filter(
        RivenMovie.viewpoint == viewpoint.id).order_by(RivenMovie.friendly)
    prev_vpt = Viewpoint.query.filter(
        Viewpoint.island == island.id,
        Viewpoint.name < viewpoint.name).order_by(Viewpoint.name.desc()).first()
    if prev_vpt:
      prev_vpt = prev_vpt.name
    next_vpt = Viewpoint.query.filter(
        Viewpoint.island == island.id,
        Viewpoint.name > viewpoint.name).order_by(Viewpoint.name.asc()).first()
    if next_vpt:
      next_vpt = next_vpt.name
    return render_template('viewpoint.html',
        images=img_query,
        movies=mov_query,
        island_name=island.title(),
        title=title,
        image_count=img_query.count(),
        movie_count=mov_query.count(),
        island_symbol=island.symbol,
        prev_vpt=prev_vpt,
        next_vpt=next_vpt)
  else:
    vpt_query=Viewpoint.query.filter(
        Viewpoint.island == island.id).order_by(Viewpoint.name)
    pos_query=Position.query.filter(
        Position.island == island.id).order_by(Position.id)
    return render_template('island.html',
        viewpoints=vpt_query,
        positions=pos_query,
        island_name=island.title(),
        island_symbol=island.symbol,
        use_unveil=True,
        position_count=pos_query.count(),
        viewpoint_count=vpt_query.count())

@app.route('/viewpoints')
@login_required
def viewpoints():
  return render_template('viewpoints.html', viewpoints=Viewpoint.query.all())

@app.route('/images')
@login_required
def images():
  return render_template('images.html', images=RivenImage.query.all())

@app.route('/protected/<path:filename>')
@login_required
def protected(filename):
  fullpath=os.path.join(app.instance_path, 'protected', filename)
  return send_from_directory(
    os.path.join(app.root_path, 'protected'),
    filename
  )

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

if __name__ == '__main__':
  if False:
    db.create_all()
    if True:
      x = Island(1, 'X', 'Test', 'mine')
      db.session.add(x)
      db.session.commit()

  debug = True
  if 'debug' in config:
    debug = str2bool(config['debug'])
  if not 'host' in config or not config['host']:
    config['host'] = '127.0.0.1'
  app.run(debug=debug, host=config['host'])
