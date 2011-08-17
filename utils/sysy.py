
import os, sys

def usage(num_args, msg):
   if len(sys.argv)-1 != num_args:
      print msg % sys.argv[0]
      sys.exit(0)

def argv(num):
   return sys.argv[num]

