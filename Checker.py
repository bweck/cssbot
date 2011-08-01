#

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import pymongo, time, logging
import reddit
from Indexer import *

class Checker:
   #
   MODS = ['surfwax95', 'RoboBama', 'bitterend']
   MAGIC_WORDS = ['solved'] #, 'found']
   #
   config = None
   mongo = None
   db = None
   collection = None
   r = None
   log = None

   #
   #
   #
   def __init__(self, config):
      self.config = config
      self.log = logging.getLogger('cssbot.Checker')
      self.mongo = pymongo.Connection()
      self.db = self.mongo[config.get("mongo", "db_name")]
      # this creates the db if n/a?
      self.collection = self.db[config.get("mongo", "collection_posts")]
      self.r = reddit.Reddit(config)
   
   #
   #
   #
   def get_next_queue_time(self, created_utc):
      now = time.time()
      age = now - created_utc;
      if age <= 3600: # 60 minutes,
         self.log.debug("post is %d old, recheck in %f", age, (age/8))
         return now + (age/8)
      else:
         self.log.debug("post is %d old, recheck in %f", age, (age/12))
         return now + (age/12)

   #
   #
   #
   def _magic_word_in(self, str):
      #print "*** searching: %s" % str
      if any(word in str.lower() for word in self.MAGIC_WORDS): 
         return True
      else:
         return False

   #
   # check to see if a post is solved.
   #
   def _is_solved_t3(self, dbrec, thing):
      #print "%s..." % (thing['data']['selftext'])[0:25]
      return self._magic_word_in(thing['data']['selftext'])

   #
   # check to see if a comment is solved
   #
   def _is_solved_t1(self, dbrec, thing):
      #print "%s..." % (thing['data']['body'])[0:25] 
      is_mw = self._magic_word_in(thing['data']['body'])
      is_author = (thing['data']['author'] == dbrec['author'])
      is_mod = (thing['data']['author'] in self.MODS)
      return is_mw and (is_author or is_mod)

   #
   #
   #
   def _walk_ds(self, dbrec, thing):
      if not thing or "kind" not in thing:
         return False;

      # grab the kind, switch off that.
      kind = thing["kind"]
      self.log.debug("processing '%s'", kind)

      # if it is a listing, enumerate the children.
      if kind == "Listing":
         if not thing['data']['children']:
            self.log.debug("reached end of line")
            return False

         # data / children
         for child in thing["data"]["children"]:
            pop = thing["data"]["children"].pop()
            return self._walk_ds(dbrec, pop) or self._walk_ds(dbrec, thing)

      # if it is a post, check the post.
      elif kind == "t3":
         #
         # search selftext
         #print "%s..." % (d['data']['selftext'])[0:25]
         return self._is_solved_t3(dbrec, thing)

      # if it is a comment, check the comment + any replies it may have.
      elif kind == "t1": 
         #
         #print "%s..." % (d['data']['body'])[0:25] 

         # check.
         if self._is_solved_t1(dbrec, thing):
            return True

         # if the comment has replies, _walk_ds that next.
         if 'replies' in thing['data']:
            return self._walk_ds(dbrec, thing['data']['replies'])

         return False

      # otherwise, say no.
      self.log.debug("skipping %s", thing)
      return False


   #
   # walk the list of items (max #?)
   #
   def run(self):
      css_dirty = False
      for rec in self.collection.find({"next_check": {"$lt": time.time()}, 'solved':'N'}).sort('created_utc', pymongo.ASCENDING):
         self.log.debug("checking id=%s title=%s", rec['id'], rec['title'].replace('\n', ' '))

         # get the latest copy of the thread
         resp = self.r.get_comments( rec['id'] )
         #print simplejson.dumps(resp, sort_keys=True, indent=3)

         # has the post been deleted?
         if resp[0]['data']['children'][0]['author'] == '[deleted]':
            Indexer index = Indexer(config)
            index.remove(rec['id'])

         #  check for solved/unsolved
         if self._walk_ds(rec, resp[0]) or self._walk_ds(rec, resp[1]):
            self.log.info("id:%s SOLVED", rec['id'])
            rec['solved'] = 'Y'
            css_dirty = True
         else:
            # requeue
            self.log.info("id:%s REQUEUED", rec['id'])
            rec['next_check'] = self.get_next_queue_time( rec['created_utc'] )

         rec['last_check'] = time.time()
         self.collection.save(rec)

      return css_dirty

