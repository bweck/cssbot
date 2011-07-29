#!/usr/bin/python

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

#
import logging, sys, os
from datetime import date
from FileLock import FileLock, FileLockException
import ConfigParser
from Indexer import *
from Checker import *
from Stylesheet import *


# make the current working directory where ever the scripts are.
abspath = os.path.abspath(sys.argv[0])
dname = os.path.dirname(abspath)
os.chdir(dname)

# create base logger
log = logging.getLogger('cssbot')
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
today = date.today()
#log_date = "%d%02d%02d" % (today.year, today.month, today.day)
log_date = "%d%02d" % (today.year, today.month)
fh = logging.FileHandler('log/cssbot-%s.log' % log_date)
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s : [%(levelname)s] %(name)s : %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)
log.addHandler(ch)


#obtain a lock.
with FileLock("update", timeout=2) as lock:

   force_css_update = False

   # read the config file.
   log.debug("loading config")
   config = ConfigParser.ConfigParser()
   config.read("cssbot.cfg")

   #
   i = Indexer(config)
   c = Checker(config)
   
   # expire old
   expire_css_dirty = i.expire()
   log.debug("css dirty due to expiration? %s", expire_css_dirty)
   
   # index new 
   i.index()
   
   # run the queue
   has_solved = c.run()
   log.debug("have new solved? %s", has_solved)
   
   # update any css if dirty css
   if force_css_update or expire_css_dirty or has_solved:
      s = Stylesheet(config)
      s.generate_and_post()

