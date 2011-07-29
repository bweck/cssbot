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

   #
   def __init__(self, config):
      self.log = logging.getLogger('cssbot.reddit')
      self.throttle = config.getfloat("reddit", "throttle")
      
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
      try:
         self.log.debug("open uri: %s", uri)
         req = Request(uri, params)
         handle = urlopen(req)
         data = handle.read()
         self.last_request_time = now
         return data
      except IOError, e:
         self.log.error("failed to open uri: %s", uri)
         if hasattr(e, 'code'):
            self.log.error('We failed with error code - %s.', e.code)
         sys.exit(1)


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



# public function postStylesheet($css, $tries=3) {
# 
#    $post = array(
#      "default_stylesheet" => "", // no need to send 36K for nothing
#      "id" => "#subreddit_stylesheet",
#      "op" => "save",
#      "r" => $this->sub,
#      "stylesheet_contents" => $css,
#      "thumbbucket" => $this->bucket,
#      "uh" => $this->uh
#    );
#  
#    $ret = Network::post("http://www.reddit.com/api/subreddit_stylesheet", $this->cookies, $post);
#    if (strpos($ret, "background")===FALSE) {
#      print "ERROR: CSS post failed: $ret\n";
#      if ($tries>0) {
#        return $this->postStylesheet($css, $tries-1);
#      } else {
#        return FALSE;
#      }
#    }
#    return TRUE;
#  }

#  public function getStylesheet() {
#    $html = $this->getReddit("/r/".$this->sub."/about/stylesheet", 0);
#    if (preg_match('{<textarea rows="20" cols="20" id="stylesheet_contents" name="stylesheet_contents" >(.*?)</textarea>}s', $html, $out)) {
#      $css = html_entity_decode($out[1]);
#      return $css;
#    }
#    return "";
#  }
      





         
####################################################
# We've now imported the relevant library - whichever library is being used urlopen is bound to the right function for retrieving URLs
# Request is bound to the right function for creating Request objects
# Let's load the cookies, if they exist. 
     
# If one of the cookie libraries is available, any call to urlopen will handle cookies using the CookieJar instance we've created
# (Note that if we are using ClientCookie we haven't explicitly imported urllib2)
# as an example :
 
#  theurl = 'http://www.reddit.com'         # an example url that sets a cookie, try different urls here and see the cookie collection you can make !
#  txdata = None                                                                           # if we were making a POST type request, we could encode a dictionary of values here - using urllib.urlencode
#  txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}          # fake a user agent, some websites (like google) don't like automated exploration
#   
#  try:
#      req = Request(theurl, txdata, txheaders)            # create a request object
#      handle = urlopen(req)                               # and open it to return a handle on the url
#  except IOError, e:
#      print 'We failed to open "%s".' % theurl
#      if hasattr(e, 'code'):
#          print 'We failed with error code - %s.' % e.code
#  else:
#      print 'Here are the headers of the page :'
#      print handle.info()                             # handle.read() returns the page, handle.geturl() returns the true url of the page fetched (in case urlopen has followed any redirects, which it sometimes does)
#   
#  print
#  if cj == None:
#      print "We don't have a cookie library available - sorry."
#      print "I can't show you any cookies."
#  else:
#      print 'These are the cookies we have received so far :'
#      for index, cookie in enumerate(cj):
#          print index, '  :  ', cookie        
#      cj.save(COOKIEFILE)                     # save the cookies again


