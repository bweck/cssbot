
#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import pymongo, time, logging
import reddit

class Stylesheet:
   #
   CSSBOT_BEGIN = '/* --- cssbot BEGIN --- */'
   CSSBOT_END =   '/* --- cssbot  END  --- */'
   #
   mongo = None
   db = None
   collection = None
   r = None
   r_sub = None
   r_user = None
   r_password = None
   log = None

   #
   #
   #
   def __init__(self, config):
      self.log = logging.getLogger('cssbot.Stylesheet')
      self.r = reddit.Reddit(config)
      self.r_user = config.get("reddit", "user")
      self.r_password = config.get("reddit", "password")
      self.r_sub = config.get("reddit", "subreddit")
      self.mongo = pymongo.Connection()
      self.db = self.mongo[config.get("mongo", "db_name")]
      self.collection = self.db[config.get("mongo", "collection_posts")]

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
         return orig

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
      _out.append("/* last modified %s */" % time.time())

      # skip up to the end marker
      for line in cursor:
         if line.startswith(self.CSSBOT_END):
            _out.append( line )
            break

      for line in cursor:
         _out.append( line )

      return '\n'.join(_out)

   def generate_and_post(self):
      # get a list of solved ids.
      solved = []
      for thing in self.collection.find({'solved':'Y'}).sort('created_utc', pymongo.ASCENDING):
         solved.append( ".id-%s a.title:before" % thing['name'] )

      self.log.debug("the solved are %s", solved)


      if solved:
         generated_css = """%s {
          content: url(%%%%tick%%%%);
          background-position: 0px 0px;
          display: inline-block;
          padding: 2px; }""" % (', '.join(solved))
      else:
         generated_css = ""

      self.log.debug("generated:\n%s", generated_css)

      #
      self.r.login(self.r_user, self.r_password)

      current_css = self.r.get_stylesheet(self.r_sub)
      self.log.info("current css\n %s", current_css)

      merged_css = self.merge_css(current_css, generated_css)

      self.log.info("updating css\n %s", merged_css)
      self.r.save_stylesheet(self.r_sub, merged_css) 


