# pyHealth Library v1.0
# Created by: Hitesh Patel <h.patel@f5.com>
# 
# This library is intended to provide a ready to use library for python that can be used with 
# the F5 iHealth service.  See the accompanying test script for examples on how to use this library
#
# This library contains no user editable config values.  

import requests, json
from json import *
from xml.etree import ElementTree
import time
import logging

# Uncomment the following to turn on full REST tracing
#try:
#	import http.client as http_client
#except ImportError:
#	import httplib as http_client
#	http_client.HTTPConnection.debuglevel = 1

DEBUG = 0
VERSION = "1.0"
USERAGENT = "pyHealth/%s" % VERSION

# enable_debug:  Enable debugging for the library
# Input: none
# Output: none
def enable_debug():
	global DEBUG
	DEBUG = 1

	logging.basicConfig() 
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True
	print "DEBUG: debug ENABLED"

# disable_debug:  Disable debugging for the library
# Input: none
# Output: none
def disable_debug():
	global DEBUG
	DEBUG = 0
	print "DEBUG: debug DISABLED"

# authenticate:  Authenticate a user to the iHealth REST API service
# Input:  STR user, STR passwd
# Output: 0=Failure
#         1=Success
def authenticate(user, passwd):
	global s
	s = requests.Session()
	s.headers.update({'User-Agent': "%s %s" % (s.headers['User-Agent'], USERAGENT)})
	payload = {'userid':user, 'passwd':passwd}
	if DEBUG: 
		print "DEBUG: authenticate: payload=",
	 	print payload

	r = s.post('https://login.f5.com/resource/loginAction.jsp', data=payload, allow_redirects=False)

	if DEBUG: 
		resp_debug(r)
		print "DEBUG: authenticate: cookies=",
		print (r.cookies)

	if not "ssosession" in r.cookies:
		if DEBUG: print "DEBUG authenticate: auth failed"
		return 0

	if DEBUG: print "DEBUG: authenticate: auth successful, ssosession=%s" % r.cookies['ssosession']

	return 1

# upload_qkview: Upload a qkview file to iHealth
# Input: STR filename
# Output: -1 File could not be opened
#		   0 iHealth did not return a valid ID
#		  >1 The ID of the qkview file in iHealth
def upload_qkview(filename):
	if DEBUG: print "DEBUG: upload_qkview: filename=%s" % filename

	try: 
		files = {'qkview': open(filename, 'rb')}
	except:
		return -1

	r = s.post('https://ihealth-api.f5.com/qkview-analyzer/api/qkviews', files=files, allow_redirects=False)

	parts = r.headers['Location'].split('/')
	
	try:
		qkviewid = int(parts.pop())
	except:
		if DEBUG: print "DEBUG: upload_qkview: ID was not an int"
		return 0

	resp_debug(r)

	if r.status_code != 303:
		if DEBUG: print "DEBUG: upload_qkview: didn't get a 303 response..."
		return 0

	return qkviewid

# get_list: Get a list of qkview ID's for the authenticated account
# Input: None
# Output: [-1]	iHealth returned a error
#		  []	iHealth returned no ID's for this account
#		  [<id1>,<id2>,...]	   List of qkview ID's
def get_list():
	if DEBUG: print "DEBUG: get_list"
	r = s.get('https://ihealth-api.f5.com/qkview-analyzer/api/qkviews')

	resp_debug(r)
	
	if r.status_code != 200:
		return [-1]

	tree = ElementTree.fromstring(r.content)

	ret = []
	for qkview in tree:
		if DEBUG: print "DEBUG: get_list: Got ID: %s" % qkview.text
		ret.append(qkview.text)

	return ret

# get_diagnostics: Get the diagnostic output report for a qkview ID (includes only heuristic HITS)
# Input: INT qkviewid
# Output: { 'code' : INT , 'content' : STR }
#	      code       content
#         200        The diagnostic report
#         999        Error string with time-out details
#         <xxx>      Error text if any was included
def get_diagnostics(qkviewid):
	if DEBUG: print "DEBUG: get_diagnostics: qkviewid=%d" % qkviewid

	return get_loop("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d/diagnostics?set=hit" % qkviewid)

# get_diagnostics_all: Get the diagnostic output report for a qkview ID (includes all heuristic HITS and MISSES)
# Input: INT qkviewid
# Output: { 'code' : INT , 'content' : STR }
#	      code       content
#         200        The diagnostic report
#         999        Error string with time-out details
#         <xxx>      Error text if any was included
def get_diagnostics_all(qkviewid):
	if DEBUG: print "DEBUG: get_diagnostics_all: qkviewid=%d" % qkviewid

	return get_loop("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d/diagnostics" % qkviewid)

# get_qkview: Get the metadata associated with a qkview ID
# Input: INT qkviewid
# Output: { '<attr_name>' : '<data>', ... }
def get_qkview(qkviewid):
	if DEBUG: print "DEBUG: get_qkview: qkviewid=%d" % qkviewid
	r = get_loop("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d" % qkviewid)

	if r['code'] != 200:
		return ""

	tree = ElementTree.fromstring(r['content'])

	ret = {}
	for attrib in tree:
		if DEBUG: print "DEBUG: get_gkview: Got KVP: %s:%s" % (attrib.tag, attrib.text)
		ret[attrib.tag] = attrib.text

	return ret

# get_loop: Perform a looping GET that is 200, 202 and 500 HTTP response code aware
# Input: STR url
# Output: { 'code' : INT , 'content' : STR }
def get_loop(url):
	if DEBUG: print "DEBUG: get_loop: url=%s" % url

	numtries = 30
	delay = 10
	counter = 1
	while True:
		if DEBUG: print "DEBUG: get_loop: trying to get url... [%d]" % counter
		r = s.get(url)

		resp_debug(r)

		if counter == numtries:
				if DEBUG: print "DEBUG: get_loop: Out of retries... counter=%d" % counter
				return {'code':'999', 'content':"Could not get report after %d tries." % numtries}
				break
		elif r.status_code == 200:
			if DEBUG: print "DEBUG: get_loop: Got a 200... counter=%d" % counter
			return {'code':r.status_code, 'content':r.content}
			break
		elif r.status_code == 202 or r.status_code == 500:
			if DEBUG: print "DEBUG: get_loop: Got a %d... counter=%d, sleeping %d" % (r.status_code,counter, delay)		
			time.sleep(delay)
			counter += 1
		else:
			if DEBUG: print "DEBUG: get_loop: Got a 500... counter=%d, sleeping %d" % (counter, delay)
			return {'code':r.status_code, 'content':r.content}
			break

# delete_qkview: Delete the qkview with the associated ID
# Input: INT qkviewid
# Output: -1   iHealth returned a error
#          1   qkview deleted
def delete_qkview(qkviewid):
	if DEBUG: print "DEBUG: delete_qkview: qkviewid=%d" % qkviewid

	r = s.delete("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d" % qkviewid)

	resp_debug(r)

	if r.status_code != 200:
		return (-1)

	return 1
	
# delete_all: Delete all qkviews in the authenticated account
# Input: None
# Output: -1   iHealth returned a error
#          1   qkview deleted	
def delete_all():
	if DEBUG: print "DEBUG: delete_all"

	r = s.delete("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews")

	resp_debug(r)

	if r.status_code != 200:
		return (-1)

	return 1
	
# set_visible: Set the visibility state of the qkview
# Input: INT qkviewid, INT visible <0,1>
# Output: 0 Error
#         1 Update completed
def set_visible(qkviewid, visible):
	if DEBUG: print "DEBUG: set_visible: qkviewid=%d visible=%d" % (qkviewid, visible)	
	if visible:
		payload = {'visible_in_gui':'true'}
	else:
		payload = {'visible_in_gui':'false'}
		
	r = s.post("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d" % qkviewid, data=payload, allow_redirects=False)

	resp_debug(r)

	if r.status_code == 200:
		return 1
	else:
		return 0

# set_share: Set the share state of the qkview
# Input: INT qkviewid, INT share <0,1>
# Output: 0 Error
#         1 Update completed
def set_share(qkviewid, share):
	if DEBUG: print "DEBUG: set_share: qkviewid=%d share=%d" % (qkviewid, share)	
	if share:
		payload = {'share_with_case_owner':'true'}
	else:
		payload = {'share_with_case_owner':'false'}
		
	r = s.post("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d" % qkviewid, data=payload, allow_redirects=False)

	resp_debug(r)

	if r.status_code == 200:
		return 1
	else:
		return 0

# set_description: Set the description of the qkview
# Input: INT qkviewid, STR description
# Output: 0 Error
#         1 Update completed
def set_description(qkviewid, descr):
	if DEBUG: print "DEBUG: set_description: qkviewid=%d description=%s" % (qkviewid, descr)	

	payload = {'description':descr}
		
	r = s.post("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d" % qkviewid, data=payload, allow_redirects=False)

	resp_debug(r)
	
	if r.status_code == 200:
		return 1
	else:
		return 0


# set_case: Set the case tag of the qkview
# Input: INT qkviewid, STR case
# Output: 0 Error
#         1 Update completed
def set_case(qkviewid, case):
	if DEBUG: print "DEBUG: set_case: qkviewid=%d case=%s" % (qkviewid, case)	

	payload = {'f5_support_case':case}
		
	r = s.post("https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/%d" % qkviewid, data=payload, allow_redirects=False)

	resp_debug(r)

	if r.status_code == 200:
		return 1
	else:
		return 0

# resp_debug: Reponse debug output
# Input: Requests r
# Output: none
def resp_debug(r):
	if DEBUG:
		print "DEBUG: resp_debug: Status code: %d" % r.status_code
		print "DEBUG: resp_debug: Request Headers: %s" % r.request.headers
		print "DEBUG: resp_debug: Response Headers: %s" % r.headers
		print "DEBUG: resp_debug: Response Content: %s" % r.content





	