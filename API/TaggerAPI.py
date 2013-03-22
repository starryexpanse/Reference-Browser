# General
import sys
from flask import g

# Utilities
import string

# API files
import Utils

# Database Connections
import Database


def search( terms ):
	g.db = Database.openDB()
	Database.closeDB(g)
	return {'hi' : 'there'}
