#!/usr/bin/env python26

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

#
import sys
import simplejson
import reddit

fetch_id = sys.argv[1]
if not fetch_id:
   print "usage: %s id" % sys.argv[0]

r = reddit.Reddit()
x = r.get_comments(fetch_id)
print simplejson.dumps(x, sort_keys=True, indent=3)

