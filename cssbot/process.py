
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import pymongo, time

from . import log, config, reddit, queue
import utils

#
# match configured magic words by author or by mod
#
class Matcher:

   matched_items = []

   #
   def __init__(self, subreddit, words=[], moderators=[]):
      self.log = log.getLogger("cssbot.process.Matcher")
      #
      self.subreddit = subreddit
      self.words = words
      self.moderators = moderators
      #
      self.reddit = reddit.APIWrapper()
      self.queue = queue.Queue()
      
   
   #
   # get a list of authorized authors which can say the magic words
   #
   def authorized_authors(self, authors=None):
      _authors = list( self.moderators )
      if isinstance(authors, list):
         _authors.extend( authors )
      else:
         _authors.append( authors )

      return _authors

   #
   #
   #
   def _magic_word_in(self, str):
      #print "*** searching: %s" % str
      if any(word in str.lower() for word in self.words): 
         return True
      else:
         return False

   #
   # check to see if a post selftext matches.
   #
   def _is_matched_t3(self, thing):
      #print "%s..." % (thing["data"]["selftext"])[0:25]
      return self._magic_word_in(thing["data"]["selftext"])

   #
   # check to see if a comment is matched
   #
   def _is_matched_t1(self, thing, authorized_authors):
      #print "%s..." % (thing["data"]["body"])[0:25] 
      is_mw = self._magic_word_in(thing["data"]["body"])
      is_aa = (thing["data"]["author"] in authorized_authors)
      return is_mw and is_aa

   #
   #
   #
   def _walk_ds(self, thing, authorized_authors):
      if not thing or "kind" not in thing:
         return False;

      # grab the kind, switch off that.
      kind = thing["kind"]
      self.log.debug("processing '%s'", kind)

      # if it is a listing, enumerate the children.
      if kind == "Listing":
         if not thing["data"]["children"]:
            self.log.debug("reached end of line")
            return False

         # data / children
         for child in thing["data"]["children"]:
            pop = thing["data"]["children"].pop()
            return self._walk_ds(pop, authorized_authors) or self._walk_ds(thing, authorized_authors)

      # if it is a post, check the post.
      elif kind == "t3":
         #
         # search selftext
         #print "%s..." % (d["data"]["selftext"])[0:25]
         return self._is_matched_t3(thing)

      # if it is a comment, check the comment + any replies it may have.
      elif kind == "t1": 
         #
         #print "%s..." % (d["data"]["body"])[0:25] 

         # check.
         if self._is_matched_t1(thing, authorized_authors):
            return True

         # if the comment has replies, _walk_ds that next.
         if "replies" in thing["data"]:
            return self._walk_ds(thing["data"]["replies"], authorized_authors)

         return False

      # otherwise, say no.
      self.log.debug("skipping %s", thing)
      return False


   #
   #
   #
   def check_thread(self, thread):
         # get the latest copy of the thread
         # check for matched/unmatched
         # update / requeue as needed.
      #
      self.log.debug("checking id=%s title=%s author=%s", thread["data"]["id"], thread["data"]["title"].replace("\n", " "), thread["data"]["author"])

      #
      authorized_authors = self.authorized_authors( thread["data"]["author"] )
      self.log.debug("authorized_authors = %s", authorized_authors)

      # get the latest copy of the thread
      resp = self.reddit.get_comments( thread["data"]["id"] )

      if not resp or len(resp) != 2:
         # most likely a json error, skip the element, leave queued up for next spin.
         return False

      #  check for matched/unmatched
      if self._walk_ds(resp[0], authorized_authors) or self._walk_ds(resp[1], authorized_authors):
         self.log.info("id:%s MATCHED", thread["data"]["id"])
         #
         thread["data"]["matched"] = "Y"
         thread["data"]["matched_ts"] = int(time.time())
         self.matched_items.append(thread)
         #
         self.queue.save(thread)
         self.queue.dequeue(thread)
         return True
      else:
         # requeue
         self.log.info("id:%s REQUEUED", thread["data"]["id"])
         self.queue.requeue(thread)
         return False
 
   #
   #
   #
   def check_items(self, threads):
      for thread in threads:
         self.check_thread(thread)

   #
   # check if the matched items have changed.
   #
   def is_dirty(self):
      #
      if self.matched_items:
         return True

      return False

   #
   #
   #
   def run(self):
      threads = self.queue.next({"data.subreddit":self.subreddit}) #, "data.matched":"N"}) #matched items are dequeued, no need to filter.
      self.check_items(threads)



