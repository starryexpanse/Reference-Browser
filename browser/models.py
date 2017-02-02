from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
test_password = None

def SetTestPassword(pwd):
  global test_password
  test_password = pwd

class Globals(db.Model, UserMixin):
  __tablename__ = 'globals'
  global_id = db.Column('global_id', db.Integer, primary_key = True)
  thumbnail_width = db.Column('thumbnail_width', db.Integer)
  thumbnail_height = db.Column('thumbnail_height', db.Integer)
  thumbnail2x_width = db.Column('thumbnail2x_width', db.Integer)
  thumbnail2x_height = db.Column('thumbnail2x_height', db.Integer)

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
    global test_password
    return password == test_password

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
  name = db.Column('name', db.String(128))
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
  left_viewpoint = db.Column('left_viewpoint',
                             db.ForeignKey('viewpoints.viewpoint_id'),
                             nullable=True)
  right_viewpoint = db.Column('right_viewpoint',
                              db.ForeignKey('viewpoints.viewpoint_id'),
                              nullable=True)
  up_viewpoint = db.Column('up_viewpoint',
                            db.ForeignKey('viewpoints.viewpoint_id'),
                            nullable=True)
  down_viewpoint = db.Column('down_viewpoint',
                             db.ForeignKey('viewpoints.viewpoint_id'),
                             nullable=True)
  forward_viewpoint = db.Column('forward_viewpoint',
                                db.ForeignKey('viewpoints.viewpoint_id'),
                                nullable=True)
  backward_viewpoint = db.Column('backward_viewpoint',
                                 db.ForeignKey('viewpoints.viewpoint_id'),
                                 nullable=True)

object_images = db.Table('object_images',
  db.Column('object', db.Integer, db.ForeignKey('objects.object_id')),
  db.Column('image', db.Integer, db.ForeignKey('rivenimgs.image_id'))
)

class RivenImage(db.Model):
  __tablename__ = 'rivenimgs'
  id = db.Column('image_id', db.Integer, primary_key = True)
  viewpoint = db.Column('viewpoint', db.ForeignKey('viewpoints.viewpoint_id'),
                        nullable=False)
  filename = db.Column(db.String(100))
  friendly = db.Column(db.String(100))
  file_path = db.Column(db.String(256))
  image_width = db.Column(db.Integer)
  image_height = db.Column(db.Integer)

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
  movie_width = db.Column(db.Integer)
  movie_height = db.Column(db.Integer)

object_movies = db.Table('object_movies',
  db.Column('object', db.Integer, db.ForeignKey('objects.object_id')),
  db.Column('movie', db.Integer, db.ForeignKey('rivenmovs.movie_id'))
)

class Object(db.Model):
  __tablename__ = 'objects'
  id = db.Column('object_id', db.Integer, primary_key = True)
  name = db.Column(db.String(100))
  title = db.Column(db.String(100))
  thumbnail = db.Column(db.String(256))
  thumbnail2x = db.Column(db.String(256))
  images = db.relationship('RivenImage', secondary=object_images,
    backref=db.backref('objects', lazy='dynamic'))
  movies = db.relationship('RivenMovie', secondary=object_movies,
    backref=db.backref('objects', lazy='dynamic'))
