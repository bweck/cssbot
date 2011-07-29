#!/usr/bin/env python26

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

#
import logging, sys, os, ConfigParser
from datetime import date
from Stylesheet import *

# make the current working directory where ever the scripts are.
abspath = os.path.abspath(sys.argv[0])
dname = os.path.dirname(abspath)
os.chdir(dname)

# create base logger
# FIXME: move into a common file.
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


# read the config file.
config = ConfigParser.ConfigParser()
config.read("cssbot.cfg")

# exec the css update.
s = Stylesheet(config)
s.generate_and_post()


