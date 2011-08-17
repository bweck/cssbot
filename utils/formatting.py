
import simplejson

def format_json(data):
   if not data:
      return data

   return simplejson.dumps(data, sort_keys=True, indent=3)

