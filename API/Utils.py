import string
import random
import re
from datetime import datetime, timedelta

def genHash(size=6):
	chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
	return ''.join(random.choice(chars) for x in range(size))


def genAuthToken(size=10):
	chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
	return ''.join(random.choice(chars) for x in range(size))


def checkReqs( requirements, arguments ):
	reqs = { 'met' : True, 'message' : '' }
	if requirements == []:
		return reqs
	for req in requirements:
		if type( req ) == list:
			if not len(set(req).intersection( arguments )):
				reqs['met'] = False
				reqs['message'] = 'either ' + str(req).strip('[]') + ' is required.'
				break
		else:
			if not req in arguments:
				reqs['met'] = False
				reqs['message'] = req + ' is required.'
				break
	return reqs

def formatTime(time, timeFormat='unix'):
	date = datetime.fromtimestamp(time)
	date = date + timedelta(hours=-6)
	
	if timeFormat == 'unix':
		return date.strftime("%s")
	elif timeFormat == 'full':
		return date.strftime("%Y-%m-%d %H:%M:%S")
	else:
		return date.strftime("%H:%M%p")

