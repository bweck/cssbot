
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import time
import pymongo

from . import log, config, reddit, queue
import utils


class Indexer:
   
   #
   #
   #
   def __init__(self, subreddit, maxage):
      self.log = log.getLogger("cssbot.index.Indexer")
      self.subreddit = subreddit
      self.maxage = maxage
      #
      self.reddit = reddit.APIWrapper()
      self.queue = queue.Queue()

   #
   #
   #
   def to_maxage(self):
      return self._index_until( self.maxage )

   #
   # index posts up to the newest post in the db
   #
   def new(self):
      last = self.queue.newest({"data.subreddit":self.subreddit})
      if not last:
         # fall back to finding all up to the maxage.
         return self.to_maxage()
      else:
         # this doesn't work properly for all cases, i.e. when items come out of the spam queue.
         return self._index_until( time.time() - last["created_ts"])


   #
   # back fill the index until maxage is reached.
   #
   def _index_until(self, age):
      self.log.info("performing an index on %s for posts newer than %d seconds.", self.subreddit, age)
      now = time.time()
      last_time = now
      last_thing = None

      #
      threads = self.reddit.get_r_new(self.subreddit)

      # walk through the pages
      #while last_time > (now - age):
      while 1:
         if not threads["data"]["children"]:
            # list is empty, fetch more.
            threads = self.reddit.get_r_new_after(self.subreddit, last_thing)
            # is the next page empty?
            if not threads:
               self.log.debug("nothing to index, empty.")
               return

         # grab the first thing.
         thing = (threads["data"]["children"]).pop(0)

         # is it older than the age to index to? stop if so.
         if (now - age) > (thing["data"]["created_utc"]):
            self.log.debug("done indexing.")
            return

         # index it.
         last_time = thing["data"]["created_utc"]
         last_thing = thing["data"]["name"]
         self._index(thing)

   #
   # index new items since pass in thing.
   #
#   def index_subreddit_since(self, thing):
#      #
#      # This methodolgy to index new things does not work properly. Sometimes posts are [deleted] 
#      #  and then index_subreddit_since does not show any. To further the problem, the results
#      #  are cached somewhere and keep giving back the author as the original user instead of 
#      #  [deleted] for some time. To workaround this situation, just index the new page every time.
#      #
#
#      #
#      threads = self.reddit.get_r_new_before(self.subreddit, thing)
#      self.log.info("indexing items %d newer than %s", len(threads["data"]["children"]), thing)
#
#      # index all of these.
#      for t in threads["data"]["children"]:
#         self._index(t)

   #
   def _index(self, thing):
      if not thing:
         return False

      #self.log.debug("indexing thing:\n%s", utils.formatting.format_json(thing))

      # sanity check - don't allow anything in older than maxage
      now = time.time()
      thing_created_utc = int(thing["data"]["created_utc"])
      if (now - thing_created_utc) > self.maxage:
         self.log.debug("skipping (%s) %s [too old]", thing["data"]["id"], thing["data"]["title"])
         return False

      # take many fields from the thing.
      x = { "name":           thing["data"]["name"],
            "id":             thing["data"]["id"],
            "subreddit":      (thing["data"]["subreddit"]).lower(),
            "subreddit_id":   thing["data"]["subreddit_id"],
            "author":         thing["data"]["author"],
            "created_utc":    thing_created_utc,
            "title":          thing["data"]["title"],
            "permalink":      thing["data"]["permalink"],
            "url":            thing["data"]["url"],
            "matched":        "N"
          }

      if not self.queue.contains({"data.id": x["id"]}):
         self.log.info("adding to index (%s) %s", x["id"], x["title"])
         return self.queue.add(x, thing_created_utc)
      else:
         self.log.debug("skipping (%s) %s", x["id"], x["title"])
         return False

#
#
#
class Expunge:

   expunged_items = []

   #
   def __init__(self, subreddit, maxage):
      self.log = log.getLogger("cssbot.index.Expunge")
      self.subreddit = subreddit
      self.maxage = maxage
      self.queue = queue.Queue()

   # remove this thing from the index.
   def _remove(self, thing):
      if not thing:
         return False

      self.log.info("removing from index %s", thing["data"]["id"])

      self.expunged_items.append(thing)
      ret = self.queue.remove(thing)
      return ret

   def is_dirty(self):
      for thing in self.expunged_items:
         if ("data" in thing) and ("matched" in thing["data"]) and (thing["data"]["matched"] == "Y"):
            return True

      return False

   # remove any posts older than maxage.
   def old(self):
      now = time.time()
      since = now - self.maxage
      self.log.debug("expiring any item older than %d in %s", since, self.subreddit)

      matched_dirty_count = self.queue.count({"data.subreddit":self.subreddit, "created_ts": {"$lt": since}, "data.matched":"Y"})
      self.log.debug("dirty count = %d", matched_dirty_count)

      for thing in self.queue.find({"data.subreddit":self.subreddit, "created_ts": {"$lt": since}}):
         self._remove( thing )

      return (matched_dirty_count > 0)

      



