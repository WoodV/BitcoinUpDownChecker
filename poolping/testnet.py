import socket
import urllib2

try:
    urllib2.urlopen('http://www.google.com/', timeout=10) 
    print "Network on!"
except urllib2.URLError as err: 
    print "Network down!"

try:
    #socket.gethostname()
    ip = socket.gethostbyname(socket.gethostname())
    print "ip is: " + ip
except socket.error as msg:
    print msg
