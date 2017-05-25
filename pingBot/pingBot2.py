import os, re,urllib2,socket,csv,datetime, time,random
from BeautifulSoup import BeautifulSoup
from netaddr import IPNetwork, IPAddress
from selenium import webdriver 
from pyvirtualdisplay import Display

HOME = '/home/mzheng/ping/pingBot2/'  # os.environ['HOME']

def getNetworkIPs(networkObj, filename):
   netf = open(filename)
   for line in netf:
      networkObj.append(line.strip())
   netf.close()
   return networkObj

networks = [] 
#networks = getNetworkIPs(networks, HOME + '/updown/data/antiDDoS/amips.txt')
#networks = getNetworkIPs(networks, HOME + '/updown/data/antiDDoS/cfips.txt')
#networks = getNetworkIPs(networks, HOME + '/updown/data/antiDDoS/incips.txt')


t = datetime.datetime.now()
ym = t.strftime('%Y-%m')
ymdh = t.strftime('%Y-%m-%d') + ':' + t.strftime('%H')
mainPath = HOME + 'data/'
htmlPath = mainPath + ym + '/' + ymdh + '/html/'
screenshotsPath = mainPath + ym + '/' + ymdh + '/screenshots/'
resultPath = HOME+'results/'+ym+'/' + ymdh
if ym not in os.listdir(mainPath):
   os.mkdir(mainPath + ym)      
if ymdh not in os.listdir(mainPath + ym + '/'):
   os.mkdir(mainPath + ym +'/' + ymdh)
if 'html' not in os.listdir(mainPath + ym +'/' + ymdh):
   os.mkdir(htmlPath)
if 'screenshots' not in os.listdir(mainPath + ym +'/' + ymdh):
   os.mkdir(screenshotsPath)
if ym not in os.listdir(HOME+'results/'):
    os.mkdir(HOME+'results/'+ym)
'''if ymdh not in os.listdir(HOME+'results/'+ym+'/'):
    os.mkdir(HOME + 'results/'+ym+'/'+ymdh)
'''
my_proxy = "129.244.245.59:23344"

def directSeleniumTest(url):
   if(url[:4] != 'http'):
      url = "http://" + url
   print "Attempting to access " + url + " through selenium..."
   #driver = webdriver.Chrome() #NO PROXY
   #driver.set_page_load_timeout(10)
   domain = stripToDomain(url)
   t = getCurrentTime()
   error = ''
   print 'here0'
   #socket.setdefaulttimeout(20)
   status = 'unsure'
   print 'here1'
   try:
      driver.get(url)
      print 'here2'
   except Exception, e:
      print e    #status = failed --- timeout
      status = 'down'
      print 'here3'
   else:
      status = findElements()
      print 'here4'

   if status != 'down':
      print 'here5'
      path = screenshotsPath + domain + '.png'
      try:                         #try to get screenshot`
         driver.save_screenshot(path)
      except Exception, e:
         print 'cannot save screenshot'
      try:                         #try to get html
         html = driver.page_source
         html=html.encode('utf-8')
         path = htmlPath + domain
         f = open(path + '.html', 'w')
         f.write(html)
         f.close()
         res=parseHTML(html)
         print res
         if len(res)>0:
            cf = [r for r in res if 'cloudflare' in r or r=='errormessage = "* Required";' or 'newrelic' in r]
            chp = [r for r in res if  "Contact your hosting provider" in r]
            if len(cf)>0 and len(chp)==0:
               status='up'
            else:
               status='down'
      except Exception, e:
         print 'cannot grab page source'
         print e
   #try:
     # print 'here7'
     # driver.close()
   #except:
   '''
   try:
      print 'here7'
      driver.quit()
   except:
      pass
   '''
   print 'here8'
   return status


def parseHTML(html):
   soup = BeautifulSoup(html)
   regex = re.compile('.*Error|error.*')
   result = regex.findall(soup.prettify())
   if 'Heroku' in html and 'No such app' in html:
      result.append('heroku')
      result.append('no such app')
   return result

def findElements():
   try:
      element = driver.find_element_by_id("errorPageContainer")
   except Exception, e: 
      return 'up'
   else: 
      print 'Found errorPageContainer' #Mozilla Firefox Error page
      return 'down'

def hitUrl(url):
   status = 'no clue'  #placeholder value
   timeout = 20
   socket.setdefaulttimeout(timeout) 
   opener = urllib2.build_opener()
   opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1')]
   domain = stripToDomain(url)
   if(url[:4] != 'http'):
      url = "http://" + url
#here
   trys = 1
   orig_url = url
   while(trys > 0 and (status == 'no clue' or status == 'down')):
      try:
         urlf = opener.open(url)
         code = urlf.getcode()
         print 'http status code: ' + str(code)
      except Exception, e:
         logError(url, e)
         print 'PING ERROR'
         print e
         status = 'down'
         if trys==3:
            url="://www.".join(url.split("://"))
         elif trys==2:
            url="https://"+url.split("://www.")[1]
         elif trys==1:
            url=orig_url
      else:
         status = "up"
         try:
            page = urlf.read()
            path = htmlPath + domain
            f = open(path + '.html', 'w')
            f.write(page)
            f.close()
         except Exception as e:
               print e
      trys = trys - 1
      time.sleep(5+random.randint(0,10))
   return status

def getUrls(filename):
   L = [] 
   if os.path.getsize(HOME + filename) <= 5:
       return L
   fl = open(HOME + filename)
   for r in csv.reader(fl, delimiter = ',', quotechar = '"'):
      if r[2]!='none':
         if r[0] == 'Currency exchanges' or r[0] == 'Bitcoin eWallets' or r[0] == 'custom' or r[0]=="Financial":
            L.append(r)
   fl.close()
   return L

def getHostByName(name):
   #subroutine of getIP()
   try:
      ip = socket.gethostbyname(name)
   except Exception, e:
      logError(name, e)
      print e
      ip = 'unknown'
   return ip

def getIP(url):
   #returns an ip address while stripping a url down to domain
   domain = stripToDomain(url)
   ip = getHostByName(domain)
   return ip

def stripToDomain(url):
   domain = ''
   if(url[:4] != 'http'):
      domain = url
   else:
      domain = url[url.index('/')+2:]
   if "/" in domain:
      domain = domain[:domain.index('/')]
   return domain
   
def getCurrentTime():
   return str(datetime.datetime.now())

def ipNetworkCheck(ip):
   for net in networks:
      if inNetwork(ip, net):
         print 'CF'
         return True
   return False

def inNetwork(ip, network):
   return IPAddress(ip) in IPNetwork(network)

def getStatus(ip,url):
   status='down'
   '''if ip== 'unknown' or not( ipNetworkCheck(ip)):
      status = hitUrl(url)
      print status
   '''
   if status == 'down' or status == 'unsure':
      status = directSeleniumTest(url)
      print status
   return status

def logError(service, error):
   #error log
   fl = open(HOME + 'errors.txt', 'a')
   t = str(datetime.datetime.now())
   message = service + ' '+t+"\n'"+str(error)+ '\n'
   fl.write(message)
   fl.close()

def ping(filename, newadd, limit):
   out = []
   urlList = getUrls(filename)
   update = []
   output = []
   outputAll = []
   if newadd != []:
       for i in newadd:
           update.append(i)
   random.shuffle(urlList)
   gottenUrls = set()
   newup = []
   for i in urlList:
      url = i[2]
      tm = i[4]
      if url in gottenUrls: continue
      gottenUrls.add(url)
      print '*---------*'
      print "url:" + url
      ip = getIP(url)
      status = getStatus(ip,url)
      t = getCurrentTime()
      u = [ url, str(80), status, t, ip]
      output.append(u)
      outputAll.append(u)
      print '^*********^'
      if status == "up":
          i[4] = datetime.datetime.now().strftime('%Y-%m-%d')
          if limit == 7:
              update.append(i)
          else:
              newup.append(i)
      elif (datetime.datetime.today() - datetime.datetime.strptime(tm, "%Y-%m-%d")).days >= limit:
        out.append(i)
      else:
        update.append(i)
   f = open(HOME + filename,'w')
   updatef = csv.writer(f, delimiter = ',', quotechar='"', quoting = csv.QUOTE_ALL, lineterminator = '\n')
   updatef.writerows(update)
   f.close()
   outputf = open(HOME + 'results/'+ym+'/'+ymdh+'.csv', 'a')
   wtr = csv.writer(outputf, delimiter = ',', quotechar='"', quoting = csv.QUOTE_ALL, lineterminator = '\n')
   wtr.writerows(output)
   outputf.close()
   outputAllf = open(HOME + 'results/resultsAll.csv', 'a')
   wtrAll = csv.writer(outputAllf, delimiter = ',', quotechar='"', quoting = csv.QUOTE_ALL, lineterminator = '\n')
   wtrAll.writerows(outputAll)
   outputAllf.close()
   return out, newup

if __name__=='__main__':
    print 'start ping at: '+ str(datetime.datetime.now())
    
    #open a virtual screen
    display = Display(visible=0, size=(800, 600))
    display.start()
    
    #set chrome proxy
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % my_proxy)
    driver = webdriver.Chrome(chrome_options=chrome_options)
    #driver = webdriver.Chrome()
    driver.set_page_load_timeout(10)

    newadd = []
    backup = []
    newadd, newback = ping('testsample.csv',newadd,7)
    backup += newback
    try:
        fh = open(HOME+'/timechecked.txt', 'r')
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
    now = datetime.datetime.now()
    if (now - datetime.datetime.strptime(timechecked[0],'%Y-%m-%d')).days >= 7 or newadd != []:
	print "Check weekly file"
        newadd, newback = ping('testsample_weekly.csv', newadd, 28)
        backup += newback
        newtime[0] = 'Last time checked weekly file:'+now.strftime('%Y-%m-%d')
    if (now - datetime.datetime.strptime(timechecked[0],'%Y-%m-%d')).days >= 30 or newadd != []:
	print "Check monthly file"
        newadd, newback = ping('testsample_monthly.csv', newadd, 90)
	if newadd != []:
            f = open(HOME + 'deadservice.csv','a')
            wtr = csv.writer(f, delimiter = ',', quotechar='"', quoting = csv.QUOTE_ALL, lineterminator = '\n')
            wtr.writerows(newadd)
            f.close()
        newtime[1] = 'Last time checked monthly file:'+now.strftime('%Y-%m-%d')
    strnewtime = '\n'.join(newtime)
    strnewtime += '\n'
    try:
        fh = open(HOME+'timechecked.txt', 'w')
    except IOError:
        print "Error: can\'t find file or read data"
        sys.exit()
    fh.write(strnewtime)
    fh.close()
    if backup != []:
        f = open(HOME+'btcservices.csv','a')
        wtr = csv.writer(f, delimiter = ',', quotechar='"', quoting = csv.QUOTE_ALL, lineterminator = '\n')
        wtr.writerows(backup)
        f.close()
    try:
        print 'here7'
        driver.quit()
    except:
        pass

    print 'END TIME: ' +str(getCurrentTime())
