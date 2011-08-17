
#
# Copyright (C) 2011 by Brian Weck
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#

import ConfigParser
import cssbot.log as log

class ConfigError(Exception):
   def __init__(self, value):
      self.value = value
   def __str__(self):
      return repr(self.value)


class Config:
   pass

class Manager:

   def __init__(self, filenames=[]):
      self._config = ConfigParser.SafeConfigParser()
      self._config.read(filenames)
      self.log = log.getLogger("cssbot.config")

   def getConfig(self):
      return self._config

   def __getValue(self, section, name, default=None):
      # if a default is specified, return that on certain errors
      if default:
         try:
            val = getConfig().get(section, name)
            self.log.debug("section %s, name %s = %s", section, name, val)
            return val
         except ConfigParser.NoOptionError, noe:
            self.log.warn("option %s not found in %s, using %s", name, section, default)
            return default
         except ConfigParser.NoSectionError, nse:
            self.log.warn("section %s not found, using %s", section, default)
            return default
         except ConfigParser.Error, e:
            raise ConfigError(e)
      else:
         # wrap all other exceptions in ours.
         try:
            return getConfig().get(section, name)
         except ConfigParser.Error, e:
            raise ConfigError(e)

   def get(self, section, name, default=None):
      return self.__getValue(section, name, default)

   def getInt(self, section, name, default=None):
      return int( self.__getValue(section, name, default) )

   def getFloat(self, section, name, default=None):
      return float( self.__getValue(section, name, default) )

   # lists are simply delimited by ,
   def getList(self, section, name, default=None, sep=","):
      # first convert default.
      val = self.__getValue(section, name, default)
      if not val or isinstance(val, list):
         return val
      # we have a delimited str.
      return val.split(sep)




Config.manager = Manager("cssbot.cfg")


def getConfig():
   return Config.manager.getConfig()

def getInt(section, name, default=None):
   return Config.manager.getInt(section, name, default)

def getFloat(section, name, default=None):
   return Config.manager.getFloat(section, name, default)

def getList(section, name, default=None):
   return Config.manager.getList(section, name, default)

def get(section, name, default=None):
   return Config.manager.get(section, name, default)

