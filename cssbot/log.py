
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import logging
from datetime import date
import utils

def __configure_logging():
   # configure the base logger for the pkg
   l = logging.getLogger("cssbot")
   l.setLevel(logging.DEBUG)

   # format.
   formatter = logging.Formatter("%(asctime)s : [%(levelname)s] %(name)s : %(message)s")

   # stdout handler.
#   ch = logging.StreamHandler()
#   ch.setLevel(logging.WARN)
#   ch.setFormatter(formatter)
#   l.addHandler(ch)

   # file handler
   today = date.today()
   log_date = "%d%02d" % (today.year, today.month) #"%d%02d%02d" % (today.year, today.month, today.day)
   fh = logging.FileHandler("log/cssbot-%s.log" % log_date)
   fh.setLevel(logging.INFO)
   fh.setFormatter(formatter)
   l.addHandler(fh)


def getLogger(name=None):
   if not name:
      name = "cssbot"

   return logging.getLogger(name)

#
utils.dirs.switch_cwd_to_script_loc()
__configure_logging()
