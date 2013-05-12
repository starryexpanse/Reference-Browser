# General
import sys

# Flask
from flask import Flask, render_template, request, redirect, url_for, Response, jsonify

# Flask Config Settings
app = Flask(__name__)
app.debug = True
domain = "0.0.0.0"

# Settings
import config

# API files
from API import tags

# Flask SQLAlchemy setting
from API.models import db
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
db.init_app(app)


# Routes
@app.route('/')
def index():
	return render_template('index.html')



@app.route('/tag/add', methods=[ 'POST' ])
def addTag():
	response = tags.add( request.json )

	# If there is an error, return appropriate error code and response ...
	if 'error' in response:                                                                                                                                   
		return jsonify({ "message" : response['message'] }), 400

	# ... otherwise return our search results.
	return jsonify( response ), 200



@app.route('/search', methods=[ 'POST' ])
def search():
	
	# Flask sets request.json to None if no request variables are passed. Parsing a 
	# None type leads to an error, so let's set it to an empty object in the absence
	# of request variables.
	request.json = request.json or {}
	
	# Search the database based off of data sent in the request
	response = tags.search( request.json )

	# If there is an error, return appropriate error code and response ...
	#if 'error' in response:                                                                                                                                   
	#	return jsonify({ "message" : response['message'] }), 400

	# ... otherwise return our search results.
	return jsonify( response ), 200


if __name__ == '__main__':
	
	# Support for optional arg to run the server on a specified port
	if len(sys.argv) > 1:
		app.run( domain, int(sys.argv[1]) )
	
	# else use default port (5000)
	else:
		app.run( domain )

