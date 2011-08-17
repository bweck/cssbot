#!/usr/bin/env python2.6

#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#


import utils
from cssbot import log, queue

#
utils.usage(1, "usage: %s id")
thing_id = utils.argv(1)

#
log = log.getLogger("cssbot.dequeue")
utils.dirs.switch_cwd_to_script_loc()


#
queue = queue.Queue()
thing = queue.contains({"data.id":thing_id})

# if we have an item, and up for queueing.
if thing and "next_ts" in thing:
   log.warn("removing item %s from queue", thing_id)
   queue.dequeue(thing)
else:
   log.error("did not remove thing %s from the queue", thing_id)


