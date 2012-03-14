#!/usr/bin/env python

from redis import Redis

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

  def __len__(self):
    if self.inprogress():
      return self._r.llen(self.queuename) + 1
    else:
      return self._r.llen(self.queuename)

  def __getitem__(self, index):
    return self._r.lrange(self.queuename, index, index)

  def inprogress(self):
    ip = self._r.lrange(self.workeritem, 0, 0)
    if ip:
      return ip.pop()
    else:
      return None

  def task_complete(self):
    logger.debug("Task completed by worker %s" % self.workername)
    return self._r.rpop(self.workeritem)

  def task_failed(self):
    logger.error("Task FAILED by worker %s" % self.workername)
    logger.debug(self.inprogress())
    return self._r.rpoplpush(self.workeritem, self.queuename)

  def push(self, item, to_queue=None):
    if to_queue:
      logger.debug("{%s} put onto queue %s by worker %s" % (item, to_queue,self.workername))
      return self._r.lpush(to_queue, item)
    else:
      logger.debug("{%s} put onto queue %s by worker %s" % (item, self.queuename,self.workername))
      return self._r.lpush(self.queuename, item)

  def pop(self):
    if self._r.llen(self.workeritem) == 0:
      self._r.rpoplpush(self.queuename, self.workeritem)
      logger.debug("{%s} pulled from queue %s by worker %s" % (self.inprogress(), self.queuename,self.workername))
    else:
      logger.debug("{%s} pulled from temporary worker queue by worker %s" % (self.inprogress(), self.workername))
    return self.inprogress()
