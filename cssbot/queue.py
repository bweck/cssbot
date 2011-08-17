
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import time
import pymongo

from . import log, config

# representation of a LIFO-ish queue using MongoDB as a datastore.
class Queue:

   # datastructure of the items in the queue are:
   # thing = 
   #  {
   #      data = <payload>,
   #      created_ts = epoch timestamp
   #      updated_ts = epoch timestamp
   #      next_ts = epoch timestamp
   #  }

   def __init__(self):
      self.log = log.getLogger("cssbot.index.Indexer")
      #
      try:
         # connect with proper URI
         self.db = pymongo.Connection( config.get("mongo", "uri") )
      except pymongo.errors.PyMongoError, e: #except pymongo.errors.InvalidURI, i:
         # connect an alternate way.
         self.db = (pymongo.Connection())[config.get("mongo", "uri")]

      self.collection = self.db[ config.get("mongo", "collection") ]

   # calculate next time the item should be checked.
   def calc_next_time(self, created_ts):
      now = time.time()
      age = now - created_ts;
      if age <= 3600: # 60 minutes,
         self.log.debug("item is %d old, recheck in %f", age, (age/8))
         return now + (age/8)
      else:
         self.log.debug("item is %d old, recheck in %f", age, (age/12))
         return now + (age/12)

   #
   #
   def add(self, payload, created_ts=None):
      now = int(time.time())
      if created_ts:
         _created_ts = created_ts
      else:
         _created_ts = now

      thing = { "data":       payload,
                "created_ts": _created_ts,
                "updated_ts": now,
                "next_ts":    now }
                
      self.collection.save(thing)
      return thing

   #
   #
   def remove(self, thing):
      if not thing["_id"]:
         return False

      ret = self.collection.remove({"_id":thing["_id"]})
      return ret
      
   # put the item back into the queue, 
   def requeue(self, thing):
      # update the timestamps.
      thing["next_ts"] = self.calc_next_time( thing["created_ts"] )
      # save.
      return self.save(thing)

   # take the item out of the next check queue.
   def dequeue(self, thing):
      # remove the next_ts
      del thing["next_ts"]
      #
      return self.save(thing)

   #
   def save(self, thing):
      thing["updated_ts"] = time.time()
      self.collection.save(thing)
      return thing

   #
   # example criteria:  { "data.subreddit": "foobar" }
   #
   def find(self, criteria=None):
      return self.collection.find(criteria)

   #
   # find the next items to process.
   #
   def next(self, criteria=None):
      if not criteria:
         criteria = {}

      # tack in the time criteria.
      criteria["next_ts"] = {"$exists": True, "$lt": time.time()}
      return self.find(criteria)

   #
   # get a list of all the items, sorted by next up in the queue.
   #
   def items(self, criteria=None):
      if not criteria:
         criteria = {}

      criteria["next_ts"] = {"$exists": True}
      return self.collection.find(criteria).sort("next_ts", pymongo.ASCENDING)

   #
   #
   #
   def count(self, criteria=None):
      return self.collection.find(criteria).count()

   # 
   # returns a find_one of the item if found, False otherwise.
   #
   def contains(self, criteria=None):
      item = self.collection.find_one(criteria)
      if item:
         return item

      return False

   #
   #
   #
   def newest(self, criteria=None):
      cursor = self.collection.find(criteria).sort("created_ts", pymongo.DESCENDING).limit(1)
      if cursor.count() != 0:
         return cursor.next()
      
      return False

   #
   #
   #
   def oldest(self, criteria=None):
      cursor = self.collection.find(criteria).sort("created_ts", pymongo.ASCENDING).limit(1)
      if cursor.count() != 0:
         return cursor.next()
      
      return False


