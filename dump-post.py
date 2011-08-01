#!/usr/bin/env python26

#
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

#
import sys
import simplejson
import reddit

if len(sys.argv) != 2:
   print "usage: %s id" % sys.argv[0]
   sys.exit(0)

fetch_id = sys.argv[1]

r = reddit.Reddit()
x = r.get_comments(fetch_id)
print simplejson.dumps(x, sort_keys=True, indent=3)

