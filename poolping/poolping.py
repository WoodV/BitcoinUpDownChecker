import os
import csv
from datetime import datetime, timedelta
import socket
import json
import time
import sys
import urllib2

'''
74.125.228.100 is one of the IP-addresses for google.com. Change http://74.125.228.100 to whatever site can 
be expected to respond quickly. Using a numerical IP-address avoids a DNS lookup, which may block the urllib2.urlopen 
call for more than a second
'''

#set the path to the poolping folder
mainPath = '/Users/mz/Documents/mz/btc/test_poolping/'

#open the src-ip file, fetch the scr IP address
'''
try:
    iprange = open(mainPath+'iprange.txt','r')
except IOError:
    print "Can't open iprange.txt file."
    sys.exit()
ips = iprange.readlines()
iprange.close()
src_ip = ips[int(ips[0][:-1])+1][:-1]
'''

def internetOn():
    try:
        response = urllib2.urlopen('http://www.google.com/', timeout=10) 
        return True
    except urllib2.URLError as err: pass
    return False

def readConfig(fname):
    names = []
    addresses = []
    ports = []
    times = []
    try:
        fh = open(mainPath+fname, 'r')
    except IOError:
        print "Error: can\'t find file or read data"
    for line in fh:
        tmp = line.split(';')
        if tmp[0] == '\n':
            break
        name = tmp[0]
        address = tmp[1]
        port = int(tmp[2])
        time = tmp[3]
        names.append(name)
        addresses.append(address)
        ports.append(port)
        times.append(time)
    return (names, addresses, ports, times)

#def pingPool(address, port, srcaddr):
def pingPool(address, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error as msg:
        print msg
        sys.exit()
    try:
        sock.settimeout(15)
        #sock.bind((srcaddr, 0))
        sock.connect((address, port))
        sock.settimeout(None)
        #uses the Stratum protocol to make a mining request
    except socket.error as msg:
        print msg
        print 'connect failed'
        status = 'down'
        return (status, msg)
    try:
        sock.send("""{"id": 1, "method": "mining.subscribe", "params": []}\n""")
        sock.settimeout(15)
        data = sock.recv(4000)
    except socket.error:
        msg = 'connected but time-out when receiving msg'
        print msg
        status = 'down'
        return (status, msg) 
    objs = data.split('\n')
    objs.pop()
    sock.close()
    if len(objs) > 0:
        status = 'up'
        return (status, 'ok') # we suppose if there are json object returned, its up and running
        for obj in objs:
            res = json.loads(obj)
            if 'error' in res:
                if res['error'] is None:
                    status = 'up'
                    return (status, 'ok')
                else:
                    # not sure if a under attack pool will able to return a error msg, save for future analysis
                    msg = res['error']
                    status = 'down'
                    return (status, msg)
    else:
        #pool returns 0 objects, under attack?
        status = 'down'
        msg = 'no objs'
        return (status, msg)
    

def dumpResult(fname, timelimit, checkout,period):
    if not internetOn():
        print 'Internet is not accessible, try later'
        sys.exit()
    now = datetime.now()
    names, addresses, ports, times = readConfig(fname)
    updatefile = ''+checkout
    uplist = ''
    if names == []:
        if not updatefile == '':
            f = open(mainPath+fname,'w')
            f.write(updatefile)
            f.close()
        return '',''
    for i in range(len(names)):
        name = names[i]
        adr = addresses[i]
        if not os.path.exists(mainPath+'Data/' + name):
            os.makedirs(mainPath+'Data/' + name)
        port = ports[i]
        lasttime = times[i]
        lasttime = lasttime[:-1]
        fl = open(mainPath+'Data/' + name + '/poolupdown_.csv', 'a')
        wtr = csv.writer(fl, delimiter = ',', quotechar='"', quoting = csv.QUOTE_MINIMAL, lineterminator = '\n')
        print 'Ping ' + adr + '...'
        #status, msg = pingPool(adr, port, src_ip)
        status, msg = pingPool(adr, port)
        # if the status is down, send the second query, to make sure it is down.
        if status == 'down':
            #status, msg = pingPool(adr, port, src_ip)
            status, msg = pingPool(adr, port)
        if status == 'up':
            lasttime = now.strftime('%Y-%m-%d %H:%M')
        ip = ''
        try:
            ip = socket.gethostbyname(adr)
        except socket.gaierror as iperror:
            print iperror
            ip = 'unknown'
        tm = str(datetime.now())
        wtr.writerow([adr, port, status, tm, ip])
        fl.close()
        # if the returned status is down, dump the msg for future analysis
        if status == 'down':
            fd = open(mainPath+'Data/' + name + '/downdetail.csv', 'a')
            dtr = csv.writer(fd, delimiter = ',', quotechar='"', quoting = csv.QUOTE_ALL, lineterminator = '\n')
            dtr.writerow([adr, port, msg, tm, ip])
            fd.close()
        time.sleep(2)
        to = datetime.strptime(lasttime,'%Y-%m-%d %H:%M')
        if (now - to).days >= timelimit:
            checkout=checkout+name+';'+adr+';'+str(port)+';'+lasttime+'\n'
        elif (now-to).days >= period:
            updatefile=updatefile+name+';'+adr+';'+str(port)+';'+lasttime+'\n'
        else:
            uplist=updatefile+name+';'+adr+';'+str(port)+';'+lasttime+'\n'
    if period == 0:
        uplist = updatefile
        return uplist, checkout
    f = open(mainPath+fname,'w')
    f.write(updatefile)
    f.close()
    return uplist, checkout

if __name__=='__main__':
    print 'Start ping at: ' + str(datetime.now())
    checkout = ''
    uplist = ''
    newup = ''
    newup, checkout = dumpResult('poolconfig.txt', 7, checkout,0)
    uplist += newup
    try:
        fh = open(mainPath+'timechecked.txt', 'r')
    except IOError:
        print "Error: can\'t find file or read data"
        sys.exit()
    timechecked = []
    newtime = []
    for line in fh:
        s = line.split(':')
        timechecked.append(s[1][:-1])
        newtime.append(line[:-1])
    fh.close()
    try:
        fh = open(mainPath+'timechecked.txt', 'w')
    except IOError:
        print "Error: can\'t find file or read data"
        sys.exit()
    now = datetime.now()
    if (now - datetime.strptime(timechecked[0],'%Y-%m-%d')).days >= 7 or checkout != '':
        newup, checkout = dumpResult('poolconfig_week.txt', 30, checkout,7)
        uplist += newup
        newtime[0] = 'Last time checked weekly file:'+now.strftime('%Y-%m-%d')
    if (now - datetime.strptime(timechecked[0],'%Y-%m-%d')).days >= 30 or checkout != '':
        newup, checkout = dumpResult('poolconfig_month.txt', 120, checkout,30)
        uplist += newup
        newtime[1] = 'Last time checked monthly file:'+now.strftime('%Y-%m-%d')
    strnewtime = '\n'.join(newtime)
    strnewtime += '\n'
    fh.write(strnewtime)
    fh.close()
    try:
        fh = open(mainPath+'poolconfig.txt', 'w')
    except IOError:
        print "Error: can\'t find file or read data"
        sys.exit()
    fh.write(uplist)
    fh.close()
    if checkout != []:
	try:
            fh = open(mainPath+'poolconfig_dead.txt','a')
	    fh.write(checkout)
	    fh.close()
	except IOError:
	    print "Can't not write to poolconfig_dead file."
    print 'End ping at:' + str(datetime.now())

