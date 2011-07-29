#!/usr/bin/env python26

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import time, ConfigParser
import pymongo

# read in config.
config = ConfigParser.ConfigParser()
config.read("cssbot.cfg")

# setup db connection
mongo = pymongo.Connection()
db = mongo[config.get("mongo", "db_name")]
collection = db[config.get("mongo", "collection_posts")]

# spin.
for thread in collection.find({'solved':'N'}).sort('next_check', pymongo.ASCENDING):
   now = time.time()
   when = thread['next_check']
   if when < now:
      when = "+"
   elif when < (now+60):
      when = "%ds" % ((when-now))
   elif when < (now+3600):
      when = "%dm" % ((when-now)/60)
   elif when < (now+86400):
      when = "%.1fh" % ((when-now)/3600)
   else:
      when = "%.1fd" % ((when-now)/86400)

   print "%s\t%s\t%s" % (when, thread['id'], (thread['title']).replace('\n', ' '))


