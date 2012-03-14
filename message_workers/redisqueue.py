#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2012 University of Oxford

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from redis import Redis
from redis.exceptions import ConnectionError
from time import sleep

WORKERPREFIX = "temp"
HOST = "localhost"
PORT = 6379
DB = 0

import logging

logger = logging.getLogger("redisqueue")
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)


"""Simple wrapper around a redis queue that gives methods in line with the other Queue-style classes"""

class RedisQueue(object):
  def __init__(self, queuename, workername, db=DB, host=HOST, port=PORT, workerprefix=WORKERPREFIX):
    self.host = host
    if isinstance(port, str):
      try:
        self.port = int(port)
      except ValueError:
        self.port = PORT
    else:
      self.port = port
    self.queuename = queuename
    self.workername = workername
    self.workeritem = ":".join([workerprefix, workername])
    self.db = db
    self._initclient()

  def _initclient(self):
    logger.info("Initialising the redis queue %s for %s" % (self.queuename, self.workername))
    logger.info("Host:%s port:%s DB:%s" % (self.host, self.port, self.db))
    logger.debug("Debug messages detailing worker queue activity")
    self._r = Redis(host=self.host, db=self.db, port=self.port)

  def check_connection(self):
    #sleep(1)
    try:
      self._r.info()
    except ConnectionError:
      self._initclient()

  def __len__(self):
    if self.inprogress():
      return self._r.llen(self.queuename) + 1
    else:
      return self._r.llen(self.queuename)

  def __getitem__(self, index):
    #self.check_connection()
    return self._r.lrange(self.queuename, index, index)

  def inprogress(self):
    #sleep(1)
    #self.check_connection()
    ip = self._r.lrange(self.workeritem, 0, 0)
    if ip:
      return ip.pop()
    else:
      return None

  def task_complete(self):
    #sleep(1)
    #self.check_connection()
    logger.debug("Task completed by worker %s" % self.workername)
    return self._r.rpop(self.workeritem)

  def task_failed(self):
    #sleep(1)
    #self.check_connection()
    logger.error("Task FAILED by worker %s" % self.workername)
    logger.debug(self.inprogress())
    return self._r.rpoplpush(self.workeritem, self.queuename)

  def push(self, item, to_queue=None):
    #sleep(1)
    #self.check_connection()
    if to_queue:
      logger.debug("{%s} put onto queue %s by worker %s" % (item, to_queue,self.workername))
      return self._r.lpush(to_queue, item)
    else:
      logger.debug("{%s} put onto queue %s by worker %s" % (item, self.queuename,self.workername))
      return self._r.lpush(self.queuename, item)

  def pop(self):
    #sleep(1)
    #self.check_connection()
    logger.debug("In pop - Queuename: %s, workeritem:%s"%(self.queuename, self.workeritem))
    if self._r.llen(self.workeritem) == 0:
      self._r.rpoplpush(self.queuename, self.workeritem)
      logger.debug("{%s} pulled from queue %s by worker %s" % (self.inprogress(), self.queuename,self.workername))
    else:
      logger.debug("{%s} pulled from temporary worker queue by worker %s" % (self.inprogress(), self.workername))
    return self.inprogress()
