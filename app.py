# Main Libraries
import sys
from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from flask.ext.sqlalchemy import SQLAlchemy


# Flask Config Settings
app = Flask(__name__)
app.debug = True
domain = "0.0.0.0"

# Flask SQLAlchemy setting
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/refBrowser'
db = SQLAlchemy(app)

# API files
import Settings
sys.path.append( Settings.API_FOLDER )
import TaggerAPI


# Routes
@app.route('/')
def index():
	return render_template('index.html')



@app.route('/tag/add', methods=[ 'POST' ])
def addTag():
	response = TaggerAPI.add( request.json )

	# If there is an error, return appropriate error code and response ...
	if 'error' in response:                                                                                                                                   
		return jsonify({ "message" : response['message'] }), 400

	# ... otherwise return our search results.
	return jsonify( response ), 200



@app.route('/search', methods=[ 'POST' ])
def search():
	
	# Flask sets request.json to None if no request variables are passed. Parsing a 
	# None type leads to an error, so let's set it to an empty object in the absense
	# of request variables.
	request.json = request.json if request.json else {}
	
	# Search the database based off of data sent in the request
	response = TaggerAPI.search( request.json )

	# If there is an error, return appropriate error code and response ...
	if 'error' in response:                                                                                                                                   
		return jsonify({ "message" : response['message'] }), 400

	# ... otherwise return our search results.
	return jsonify( response ), 200


if __name__ == '__main__':
	
	# Support for optional arg to run the server on a specified port
	if len(sys.argv) > 1:
		app.run( domain, int(sys.argv[1]) )
	
	# else use default port (5000)
	else:
		app.run( domain )

