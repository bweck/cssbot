
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import sys, os.path, time, re
import urllib, urllib2, cookielib
import simplejson, HTMLParser
from urlparse import urlparse

from HTTPHeaderLogger import HTTPHeaderLoggerHandler
from . import log, config

class APIWrapper:
   """ APIWrapper for reddit """

   #
   last_request_time = None

   #
   def __init__(self):
      self.log = log.getLogger("cssbot.reddit.APIWrapper")
      #
      self.throttle = config.getFloat("reddit", "throttle", 2.5)
      self.num_retries = config.getInt("reddit", "num_retries", 3)
      self.retry_delay_sec = config.getFloat("reddit", "retry_delay_sec", 15)
      self.user = config.get("reddit", "user")
      self.password = config.get("reddit", "password")
      #
      self.cj = cookielib.CookieJar()
      self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj), HTTPHeaderLoggerHandler)
      urllib2.install_opener(self.opener)


   # https://github.com/reddit/reddit/wiki/API%3A-login
   def login(self):
      #
      uri = "http://www.reddit.com/api/login/%s" % self.user
      params = urllib.urlencode(dict(api_type="json", user=self.user, passwd=self.password))
      j = self.make_request_json(uri, params)

      #FIXME: throw errors?
      errors = j["json"]["errors"]
      if errors:
         self.log.error( "Login failed: [%s] %s", errors[0][0], errors[0][1])
         sys.exit(1)

      self.modhash = j["json"]["data"]["modhash"]
      self.log.debug( "modhash = %s", self.modhash )

      self.cookie = j["json"]["data"]["cookie"]
      self.log.debug( "cookie = %s", self.cookie )
      self.log.debug( "cookiejar = %s", self.cj )

      return True

   # logout.
   def logout(self):
      self.cj.clear()
      return True


   #
   #
   def make_request_json(self, uri, params=None):
      #
      parts = urlparse(uri)

      # scheme://netloc/path;parameters?query#fragment
      _uri = parts.scheme + "://" + parts.netloc + parts.path

      if not parts.path.endswith(".json"):
         _uri += ".json"

      if parts.params:
         _uri += ";" + parts.params

      if parts.query:
         _uri += "?" + parts.query

      if parts.fragment:
         _uri += "#" + parts.fragment

      #
      content = self.make_request(_uri, params)
      try:
         return simplejson.loads(content)
      except simplejson.decoder.JSONDecodeError, jde:
         self.log.error("could not parse json response, stopping. content=\n%s", content)
         sys.exit(1)

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
      while 1:
         try:
            self.log.debug("open uri: %s", uri)
            req = urllib2.Request(uri, params)
            handle = urllib2.urlopen(req)
            data = handle.read()
            self.last_request_time = now
            return data
         except IOError, e:
            self.log.warn("failed to open uri: %s", uri)
            if hasattr(e, "code"):
               self.log.warn("We failed with error code - %s.", e.code)

            #
            if attempts > self.num_retries:
               self.log.error("attempt to open uri %s failed %d times, exiting.", uri, attempts)
               # alternatively, re-throw the error to catch at a higher level.
               sys.exit(1)

            #
            attempts += 1
            self.log.warn("retrying %s in %d sec", uri, self.retry_delay_sec)
            time.sleep(self.retry_delay_sec)

      # finally,
      return None


   def get_stylesheet(self, sub):
      contents = self.make_request("http://www.reddit.com/r/%s/about/stylesheet" % sub)

      if not contents:
         self.log.error("could not get a current copy of the css, exiting")
         sys.exit(1)
      
      p = re.compile('<textarea rows="20" cols="20" id="stylesheet_contents" name="stylesheet_contents" >(.*?)</textarea>')
      m = p.search(contents)
      css = m.group(1)
      h = HTMLParser.HTMLParser()
      return h.unescape(css)

   def save_stylesheet(self, sub, css):
      d = dict( id="#subreddit_stylesheet",
                op="save",
                r=sub,
                renderstyle="html",
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

