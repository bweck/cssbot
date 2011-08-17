
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import time
from . import log, reddit, queue

class Stylesheet:

   #
   CSSBOT_PAUSE = "/* --- cssbot action PAUSE --- */"
   CSSBOT_BEGIN = "/* --- cssbot BEGIN --- */"
   CSSBOT_END =   "/* --- cssbot  END  --- */"
   #


   #
   #
   #
   def __init__(self, subreddit, selector, rule):
      self.log = log.getLogger("cssbot.style.Stylesheet")
      #
      self.subreddit = subreddit
      self.selector = selector
      self.rule = rule
      #
      self.reddit = reddit.APIWrapper()
      self.queue = queue.Queue() 

   #
   #
   #
   def merge_css(self, orig="", update=""):
      _out = []

      # look for the markers, do nothing if not found.
      try:
         orig.index(self.CSSBOT_BEGIN) 
         orig.find(self.CSSBOT_END)
      except ValueError:
         # return original string
         self.log.warn("could not find start/end markers.")
         return False

      # parse the stylesheet
      lines = orig.splitlines()

      #
      cursor = iter(lines)

      # pre begin lines.
      for line in cursor:
         _out.append( line )
         if line.startswith(self.CSSBOT_BEGIN):
            break

      # add marker/new css
      _out.append(update)
      _out.append("")
      _out.append("/* last modified %s */" % int(time.time()))

      # skip up to the end marker
      for line in cursor:
         if line.startswith(self.CSSBOT_END):
            _out.append( line )
            break

      for line in cursor:
         _out.append( line )

      return "\n".join(_out)

   #
   # check if this css has the pause command in it.
   #
   def is_paused(self, css):
      try:
         if css:
            css.index(self.CSSBOT_PAUSE)
            return True
      except ValueError:
         pass

      return False

   #
   #
   #
   def generate_and_save(self):
      # login to reddit.
      self.reddit.login()

      # get the current css.
      current_css = self.reddit.get_stylesheet(self.subreddit)
      if self.is_paused(current_css):
         self.log.warn("not updating css, paused.")
         return False

      self.log.info("current css:\n %s", current_css)

      # get a list of matched thing names.
      matched_names = []
      matched_snippet = []
      for thing in self.queue.find({"data.matched":"Y"}):
         name = thing["data"]["name"]
         matched_names.append(name)
         matched_snippet.append( ".id-%s %s" % (name, self.selector) )

      self.log.debug("the matched are %s", matched_names)

      if matched_snippet:
         generated_css = "%s %s" % ( (", ".join(matched_snippet)), self.rule )
      else:
         generated_css = ""

      self.log.debug("generated:\n%s", generated_css)


      # merge the new and current css.
      merged_css = self.merge_css(current_css, generated_css)

      # save the css.
      if merged_css:
         self.log.info("saving css:\n %s", merged_css)
         self.reddit.save_stylesheet(self.subreddit, merged_css) 


