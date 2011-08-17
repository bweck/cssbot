#!/usr/bin/env python2.6

#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import utils
from cssbot import log, config
from cssbot import index 
from cssbot import process
from cssbot import style

#
utils.dirs.switch_cwd_to_script_loc()
log = log.getLogger("cssbot")

#
subreddits = config.getList("cssbot", "subreddits")
try:
   with utils.FileLock("update", timeout=2) as lock:
      log.debug("got lock")

      for subreddit in subreddits:
         # get configured values for the subreddit
         maxage = config.getInt(subreddit, "maxage")
         words = config.getList(subreddit, "words")
         moderators = config.getList(subreddit, "moderators")
         selector = config.get(subreddit, "style_selector")
         rule = config.get(subreddit, "style_rule")

         # setup.
         expunge = index.Expunge(subreddit, maxage)
         index = index.Indexer(subreddit, maxage)
         matcher = process.Matcher(subreddit, words, moderators)

         # process.
         expunge.old() 
         index.new()
         matcher.run()

         # update the css?
         if expunge.is_dirty() or matcher.is_dirty():
            stylesheet = style.Stylesheet(subreddit, selector, rule)
            stylesheet.generate_and_save()

except utils.FileLockException as e:
   log.warn("unable to obtain lock, probable cause is another process executing")
      

