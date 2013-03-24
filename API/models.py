from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.schema import UniqueConstraint

db = SQLAlchemy()

## Models
class Asset(db.Model):
	__tablename__ = 'assets'
	id = db.Column(db.Integer, primary_key = True)
	type = db.Column(db.VARCHAR(64))
	filename = db.Column(db.VARCHAR(64))

class Tag(db.Model):
	__tablename__ = 'tags'
	id = db.Column(db.Integer, primary_key = True)
	value = db.Column(db.VARCHAR(64), unique=True)
