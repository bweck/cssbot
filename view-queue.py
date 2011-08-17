#!/usr/bin/env python2.6

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#


import time, os
from datetime import timedelta 

from cssbot import log, queue
import utils


def humanize_time(secs): 
   #
   if secs < 0:
      return "+"
   # no need for millis.
   secs = int(secs)
   d = timedelta(seconds=secs) 
   return str(d)


#
utils.dirs.switch_cwd_to_script_loc()
log = log.getLogger("cssbot")

#
now = time.time()
queue = queue.Queue()
for item in queue.items():
   #
   rows, cols = os.popen('stty size', 'r').read().split()
   cols = int(cols)
   #
   # left_padding_len is the length of all the preceding text + paddings.
   left_padding_len = 52
   if len(item["data"]["title"]) > (cols-left_padding_len):
      title = "%s..." % (item["data"]["title"]).replace("\n", " ")[:(cols-left_padding_len-3)]
   else:
      title = "%s" % (item["data"]["title"]).replace("\n", " ")

   print "%-15s   %s in r/%-20s   %s" % (humanize_time(item["next_ts"]-now), item["data"]["id"], item["data"]["subreddit"], title)

