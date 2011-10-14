#!/usr/bin/env python

import ConfigParser, os

class Config(ConfigParser.ConfigParser):
  DEFAULT_CONFIG_FILE = "loglines.cfg"
  def __init__(self, config_file=DEFAULT_CONFIG_FILE):
    ConfigParser.ConfigParser.__init__(self)
    if os.path.exists(config_file) and os.path.isfile(config_file):
      self.read(config_file)
      self.validate()

  def validate(self):
    pass
