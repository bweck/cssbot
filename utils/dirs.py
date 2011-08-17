
import os, sys

# switch the cwd to the script location.
def switch_cwd_to_script_loc():
   abspath = os.path.abspath(sys.argv[0])
   dname = os.path.dirname(abspath)
   os.chdir(dname)
   


