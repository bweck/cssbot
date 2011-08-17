#!/usr/bin/env python2.6

#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

#
import utils
from cssbot import reddit

utils.usage(1, "usage: %s id")
fetch_id = utils.argv(1)

r = reddit.APIWrapper()
r.num_retries = 0
x = r.get_comments(fetch_id)
print utils.format_json(x)

