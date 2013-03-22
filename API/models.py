from app import db

## Tag models
class Tag(db.Model):
	__tablename__ = 'tags'
	id = db.Column(db.Integer, primary_key = True)
	value = db.Column(db.VARCHAR(64), unique=True)
