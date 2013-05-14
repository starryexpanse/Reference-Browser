import sqlite3

DATABASE = 'database.db'

def openDB():
	return sqlite3.connect(DATABASE)

def closeDB(g):
	if hasattr(g, 'db'):
		g.db.close()
