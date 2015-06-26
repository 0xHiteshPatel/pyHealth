#!/usr/bin/python

import pyHealth
import time
import getpass
import sys

if len(sys.argv) != 2:
	print "Usage: %s <qkview file>" % sys.argv[0]
	quit(0)

# Uncomment the following to enable debug output from the library
pyHealth.enable_debug()

username = raw_input('Enter iHealth Username: ')
password = getpass.getpass('Enter iHealth Password: ')

# Authenticate with the iHealth service
print "Authenticating to iHealth..."
if not pyHealth.authenticate(username,password):
	print "iHealth Auth Failed"
	quit(0)

# Upload a local qkview file to the service.

print "Uploading qkview to iHealth..."
qkviewid = pyHealth.upload_qkview(sys.argv[1])
if qkviewid <= 0:
	print "File upload failed"
	quit(0)

print "Uploaded iHealth QKView ID is %d\n" % qkviewid

print "Details:",
print pyHealth.get_qkview(qkviewid)

# Set the qkview to visible in the iHealth GUI
print "Setting visible... "
print pyHealth.set_visible(qkviewid, 1)

# Set the qkview to shareable with F5 support
print "Setting shareable... "
print pyHealth.set_share(qkviewid, 1)

# Set the qkview descriptions
print "Setting description... "
print pyHealth.set_description(qkviewid, "My description")

# Set the F5 support case number associated with the qkview
print "Setting case number... "
print pyHealth.set_case(qkviewid, "C123456")

# Show updated metadata
print "\nUpdated Details:",
print pyHealth.get_qkview(qkviewid)

# Get a list of qkviews
print "\nList of qkviews in this account"
mylist = pyHealth.get_list()
print mylist

# Get diagnostics output.  We have to check the response code from iHealth
print "Diagnostics output:"
print pyHealth.get_diagnostics(qkviewid)

# Get full diagnostics output (including heuristic misses)
print "\n\nDiagnostics output (inluding misses):"
print pyHealth.get_diagnostics_all(qkviewid)

print "\nDeleting uploaded qkview"
print pyHealth.delete_qkview(qkviewid)

print "Deleting all qkviews"
print pyHealth.delete_all()
