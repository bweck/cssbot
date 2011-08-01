#

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import os.path
import urllib
import simplejson
import sys
import time
import re
import HTMLParser
from urlparse import urlparse
import logging

cj = None
ClientCookie = None
cookielib = None
 
try:                                    # Let's see if cookielib is available
    import cookielib            
except ImportError:
    pass
else:
    import urllib2    
    urlopen = urllib2.urlopen
    #cj = cookielib.LWPCookieJar()       # This is a subclass of FileCookieJar that has useful load and save methods
    cj = cookielib.CookieJar()       # This is a subclass of FileCookieJar that has useful load and save methods
    Request = urllib2.Request
 
if not cookielib:                   # If importing cookielib fails let's try ClientCookie
    try:                                            
        import ClientCookie 
    except ImportError:
        import urllib2
        urlopen = urllib2.urlopen
        Request = urllib2.Request
    else:
        urlopen = ClientCookie.urlopen
        #cj = ClientCookie.LWPCookieJar()
        cj = ClientCookie.CookieJar()
        Request = ClientCookie.Request


class Reddit:
   """ r e d d i t """

   # the path and filename that you want to use to save your cookies in
   COOKIEFILE = 'cookies.lwp'
   throttle = 2.5
   last_request_time = None
   log = None
   num_retries = 3
   retry_delay_sec = 15

   #
   def __init__(self, config):
      self.log = logging.getLogger('cssbot.reddit')
      self.throttle = config.getfloat("reddit", "throttle")

      if config.get('reddit', 'num_retries'):
         num_retries = config.getInt('reddit', 'num_retries')

      if config.get('reddit', 'retry_delay_sec'):
         num_retries = config.getFloat('reddit', 'retry_delay_sec')
      
      # now we have to install our CookieJar so that it is used as the default CookieProcessor in the default opener handler
      if cj != None:                                  
#          if os.path.isfile(self.COOKIEFILE):
#              cj.load(self.COOKIEFILE)
          if cookielib:
              opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
              urllib2.install_opener(opener)
          else:
              opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
              ClientCookie.install_opener(opener)
 

   def login(self, user, passwd):
      #
      self.user = user

      uri = "http://www.reddit.com/api/login"
      params = urllib.urlencode(dict(api_type='json', user=self.user, passwd=passwd))
      j = self.make_request_json(uri, params)

      #FIXME: check errors.
      errors = j['json']['errors']

      if errors:
         self.log.error( "Login failed: [%s] %s", errors[0][0], errors[0][1])
         sys.exit(1)

      self.modhash = j['json']['data']['modhash']
      self.cookie = j['json']['data']['cookie']

      self.log.debug( "modhash = %s", self.modhash )
      self.log.debug( "cookie = %s", self.cookie )
      self.log.debug( "cj = %s", cj )

      return True

   #
   #
   def make_request_json(self, uri, params=None):
      #
      parts = urlparse(uri)

      # scheme://netloc/path;parameters?query#fragment
      _uri = parts.scheme + "://" + parts.netloc + parts.path

      if not parts.path.endswith('.json'):
         _uri += ".json"

      if parts.params:
         _uri += ";" + parts.params

      if parts.query:
         _uri += "?" + parts.query

      if parts.fragment:
         _uri += "#" + parts.fragment

      #
      content = self.make_request(_uri, params)
      return simplejson.loads(content)

   #
   #
   def make_request(self, uri, params=None):
      #
      now = time.time()
      if self.last_request_time is not None:
         if now < (self.last_request_time + self.throttle):
            duration = (self.last_request_time + self.throttle) - now
            self.log.debug("delaying %s seconds until next request", duration)
            time.sleep(duration)
      #
      attempts = 1
      while attempts <= num_retries:
         try:
            self.log.debug("open uri: %s", uri)
            req = Request(uri, params)
            handle = urlopen(req)
            data = handle.read()
            self.last_request_time = now
            return data
         except IOError, e:
            self.log.warn("failed to open uri: %s", uri)
            if hasattr(e, 'code'):
               self.log.warn('We failed with error code - %s.', e.code)
            #
            if attempts > num_retries:
               self.log.error('attempt to open uri %s failed %d times, exiting.' % (uri, attempts))
               # alternatively, re-throw the error to catch at a higher level.
               sys.exit(1)
            #
            attempts += 1
            time.sleep(retry_delay_sec)


   def get_stylesheet(self, sub):
      contents = self.make_request('http://www.reddit.com/r/%s/about/stylesheet' % sub)
      p = re.compile('<textarea rows="20" cols="20" id="stylesheet_contents" name="stylesheet_contents" >(.*?)</textarea>')
      m = p.search(contents)
      css = m.group(1)
      h = HTMLParser.HTMLParser()
      return h.unescape(css)

   def save_stylesheet(self, sub, css):
      d = dict( id='#subreddit_stylesheet',
                op='save',
                r=sub,
                renderstyle='html',
                stylesheet_contents=css,
                uh=self.modhash )

      params = urllib.urlencode(d)

      return self.make_request("http://www.reddit.com/api/subreddit_stylesheet", params)

   def get_comments(self, thing_id):
      uri = "http://www.reddit.com/comments/%s" % thing_id
      return self.make_request_json(uri)

   def get_r_new(self, subreddit):
      uri = "http://www.reddit.com/r/%s/new/?sort=new" % (subreddit)
      return self.make_request_json(uri)

   def get_r_new_before(self, subreddit, t3):
      uri = "http://www.reddit.com/r/%s/new/?sort=new&before=%s" % (subreddit, t3)
      return self.make_request_json(uri)

   def get_r_new_after(self, subreddit, t3):
      uri = "http://www.reddit.com/r/%s/new/?sort=new&after=%s" % (subreddit, t3)
      return self.make_request_json(uri)

