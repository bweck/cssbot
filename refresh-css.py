#!/usr/bin/env python2.6

#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#


import utils
from cssbot import log, config, style

#
log = log.getLogger("cssbot")

#
subreddits = config.getList("cssbot", "subreddits")
for subreddit in subreddits:
   #
   log.warn("forcing update of stylesheet for %s", subreddit)

   # get configured values for the subreddit
   selector = config.get(subreddit, "style_selector")
   rule = config.get(subreddit, "style_rule")

   # update the css.
   stylesheet = style.Stylesheet(subreddit, selector, rule)
   stylesheet.generate_and_save()


