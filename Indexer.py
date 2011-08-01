
#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import pymongo
import time, random, logging
import reddit


class Indexer:
   
   sub = None
   duration = None
   mongo = None
   db = None
   collection = None
   r = None
   log = None

   def __init__(self, config):
      self.log = logging.getLogger('cssbot.Indexer')
      self.sub = config.get("reddit", "subreddit")
      self.duration = config.getint("indexer", "duration")
      self.mongo = pymongo.Connection()
      self.db = self.mongo[config.get("mongo", "db_name")]
      # this creates the db if n/a?
      self.collection = self.db[config.get("mongo", "collection_posts")]
      self.r = reddit.Reddit(config)

   def index_full(self):
      self.log.info("performing a full index")
      now = time.time()
      last_time = now
      last_thing = None

      #
      threads = self.r.get_r_new(self.sub)

      while last_time > (now - self.duration):
         if not threads['data']['children']:
            # list is empty, fetch more.
            threads = self.r.get_r_new_after(self.sub, last_thing)

         thing = (threads['data']['children']).pop(0)
         last_time = thing['data']['created_utc']
         last_thing = thing['data']['name']

         self._index(thing)

   def index_since(self, name):
      #
      threads = self.r.get_r_new_before(self.sub, name)
      self.log.info("indexing items %d newer than %s", len(threads['data']['children']), name)

      # index all of these.
      for thing in threads['data']['children']:
         self._index(thing)


   def _index(self, thing):
      if not thing:
         return False

      now = time.time()
      x = { 'name':        thing['data']['name'],
            'id':          thing['data']['id'],
            'author':      thing['data']['author'],
            'created_utc': thing['data']['created_utc'],
            'title':       thing['data']['title'],
            'url':         thing['data']['url'],
            'solved':      'N',
            'next_check':  now,
            'added':       now
          }

      if not self.collection.find_one({"id": x['id']}):
         self.log.info("adding to index (%s) %s", x['id'], x['title'])
         self.collection.insert(x)
      else:
         self.log.warn("skipping (%s) %s", x['id'], x['title'])

   def index(self):
      self.log.debug("index()")
      count = self.collection.count()
      self.log.debug("index contains %s items", count)
      if count == 0:
         self.index_full()
      else:
         p = self.collection.find().sort('created_utc', pymongo.DESCENDING).limit(1).next()
         self.index_since(p['name'])

   # remove this thing by id from the index.
   def remove(self, thing_id):
      if not thing:
         return False

      log.info("removing from index id=%s" % thing_id)

      # FIXME: handle errors, safe=, etc.
      return self.collection.remove({'id':thing_id})


   # remove any posts older than duration.
   def expire(self):
      self.log.debug("expire()")
      now = time.time()
      since = now - self.duration
      self.log.debug("expiring any item older than %d", since)
      solved_dirty_count = self.collection.find({"created_utc": {"$lt": since}, 'solved':'Y'}).count()
      for thing in self.collection.find({"created_utc": {"$lt": since}}).sort('created_utc', pymongo.ASCENDING):
         self.log.debug("removing from index (%s)[%s] %s", thing['id'], thing['solved'], thing['title'])
         self.collection.remove( thing )

      return (solved_dirty_count > 0)

      



