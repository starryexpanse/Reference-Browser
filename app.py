# Main Libraries
import sys
from flask import Flask, render_template, request, redirect, url_for, Response
import json
from bson import json_util

# API files
import Settings
sys.path.append( Settings.API_FOLDER )
import TaggerAPI, Utils

# Flask Config Settings
app = Flask(__name__)
app.debug = True
domain = "0.0.0.0"


# Routes
@app.route('/')
def index():
	return render_template('index.html')



@app.route('/addTag', methods=[ 'POST' ])
def addTag():
	return {}


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
		error = json.dumps({ "error" : True, "message" : response['message'] })
		resp = Response( error, status=400, mimetype='application/json' ) 
		resp.headers['Link'] = request.url
		return resp

	# ... otherwise return our search results.
	js = json.dumps( response ) 
	resp = Response( js, status=200, mimetype='application/json' )
	resp.headers['Link'] = request.url

	return resp



if __name__ == '__main__':
	
	# Support for optional arg to run the server on a specified port
	if len(sys.argv) > 1:
		app.run( domain, int(sys.argv[1]) )
	
	# else use default port (5000)
	else:
		app.run( domain )

