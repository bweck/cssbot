
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import httplib, urllib2, logging

class HTTPHeaderLoggerConnection(httplib.HTTPConnection):
   def send(self, s):
      log = logging.getLogger("cssbot.reddit.http")
      log.debug("request headers\n%s", s)   # or save them, or whatever!
      httplib.HTTPConnection.send(self, s)

class HTTPHeaderLoggerHandler(urllib2.HTTPHandler):
   def http_open(self, req):
      log = logging.getLogger("cssbot.reddit.http")
      handle = self.do_open(HTTPHeaderLoggerConnection, req)
      log.debug("response headers\n%s", handle.info())
      return handle



