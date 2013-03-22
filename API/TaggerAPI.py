# General
import sys
from flask import g

# Utilities
import string

# Database Models
import models

# Database
from app import db

def add( tag ):
	u = models.Tag(value=tag['value'])
	db.session.add(u)
	db.session.commit()
	return { 'success' : True }

def search( terms ):
	return {'hi' : 'there'}
