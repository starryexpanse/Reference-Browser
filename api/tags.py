# General
import sys

# Database Models
import models

def add( request ):
	u = models.Asset(type=request['type'], filename=request['filename'])
	db.session.add(u)
	db.session.commit()
	return { 'success' : True }

def search( request ):
	results = models.Asset.query.filter_by(type=request['term']).first()
	if results is None:
		return {}
	return results
