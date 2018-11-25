from flask import (
  Blueprint,
  flash,
  redirect,
  render_template,
  request,
  safe_join,
  send_from_directory,
  url_for
)
from flask_login import (
  current_user,
  LoginManager,
  login_required,
  login_user,
  logout_user
)
from flask_wtf import FlaskForm
from browser.models import (
  Globals,
  Island,
  Position,
  RivenImage,
  RivenMovie,
  User,
  Viewpoint
)
from urlparse import urlparse, urljoin
from wtforms import StringField, PasswordField, validators
import json

browsing = Blueprint('browsing', __name__,
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='/browsing/static')

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'browsing.login'

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

@browsing.route('/')
@login_required
def islands():
  query = Island.query.order_by(Island.symbol).all()
  return render_template('islands.html',
    islands=query,
    title='')

@browsing.route('/login', methods=['GET', 'POST'])
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
      return browsing.abort(400)

    return redirect(next or url_for('browsing.islands'))
  return render_template('login.html', form=form)

@browsing.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for('browsing.islands'))

@browsing.route('/island/<symbol>', strict_slashes=False)
@login_required
def island(symbol):
  g = Globals.query.filter(Globals.global_id == 1).first()
  island = Island.query.filter(Island.symbol == symbol).first()
  if not island:
    return 'There is no "%s" island.' % symbol

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
      viewpoint_count=vpt_query.count(),
      title=island.title(),
      thumbnail_width=g.thumbnail_width,
      thumbnail_height=g.thumbnail_height,
      thumbnail2x_width=g.thumbnail2x_width,
      thumbnail2x_height=g.thumbnail2x_height)

def GetViewpointMatrix(viewpoint):
  return {
    'island_symbol': chr(viewpoint.island),
    'viewpoint_name': viewpoint.name,
    'thumbnail': viewpoint.thumbnail,
    'thumbnail2x': viewpoint.thumbnail2x
  }

def LoadViewpoint(viewpoint_id):
  return Viewpoint.query.filter(Viewpoint.id == viewpoint_id).first()

def FillViewpointMatrixColumn(m, viewpoint, col):
  if viewpoint.up_viewpoint:
    m[0][col] = GetViewpointMatrix(LoadViewpoint(viewpoint.up_viewpoint))
  m[1][col] = GetViewpointMatrix(viewpoint)
  if viewpoint.down_viewpoint:
    m[2][col] = GetViewpointMatrix(LoadViewpoint(viewpoint.down_viewpoint))

def CreateViewpointMatrix(viewpoint):
  # LU, CU, RU, RRU
  # L , C , R , RR
  # LL, CL, RL, RRL
  m = [[None for x in range(4)] for y in range(3)]
  FillViewpointMatrixColumn(m, viewpoint, 1)
  if viewpoint.left_viewpoint:
    FillViewpointMatrixColumn(m, LoadViewpoint(viewpoint.left_viewpoint), 0)
  if viewpoint.right_viewpoint:
    right_viewpoint = LoadViewpoint(viewpoint.right_viewpoint)
    FillViewpointMatrixColumn(m, right_viewpoint, 2)
    if right_viewpoint.right_viewpoint:
      FillViewpointMatrixColumn(m, LoadViewpoint(right_viewpoint.right_viewpoint), 3)

  return m

@browsing.route('/island/<symbol>/viewpoint/<vpt_name>', strict_slashes=False)
@login_required
def viewpoint(symbol, vpt_name):
  g = Globals.query.filter(Globals.global_id == 1).first()
  island = Island.query.filter(Island.symbol == symbol).first()
  if not island:
    return 'There is no "%s" island.' % symbol

  viewpoint = Viewpoint.query.filter(Viewpoint.island == island.id,
                                     Viewpoint.name == vpt_name).first()
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

  vpt_matrix = CreateViewpointMatrix(viewpoint)

  return render_template('viewpoint.html',
      images=img_query,
      movies=mov_query,
      island_name=island.title(),
      title=title,
      image_count=img_query.count(),
      movie_count=mov_query.count(),
      island_symbol=island.symbol,
      prev_vpt=prev_vpt,
      next_vpt=next_vpt,
      thumbnail_width=g.thumbnail_width,
      thumbnail_height=g.thumbnail_height,
      vpt_matrix=json.dumps(vpt_matrix))

@browsing.route('/viewpoints')
@login_required
def viewpoints():
  return render_template('viewpoints.html', viewpoints=Viewpoint.query.all())

@browsing.route('/images')
@login_required
def images():
  return render_template('images.html', images=RivenImage.query.all())

@browsing.route('/protected/<path:filename>')
@login_required
def protected(filename):
  d = safe_join(browsing.root_path, 'protected')
  return send_from_directory(d, filename)
