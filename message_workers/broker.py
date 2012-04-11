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

from redisqueue import RedisQueue

from LogConfigParser import Config

import sys

from time import sleep

if __name__ == "__main__":
  c = Config()
  redis_section = "redis"
  worker_section = "worker_broker"
  worker_number = sys.argv[1]
  if len(sys.argv) == 3:
    if "redis_%s" % sys.argv[2] in c.sections():
      redis_section = "redis_%s" % sys.argv[2]

  rq = RedisQueue(c.get(worker_section, "listento"), "broker_%s" % worker_number,
                  db=c.get(redis_section, "db"), 
                  host=c.get(redis_section, "host"), 
                  port=c.get(redis_section, "port")
                  )
  if c.has_option(worker_section, "fanout_status_queue"):
    # keep a queue of messages to deliver for a given push'd item
    # better resumeability at the cost of more redis operations
    topushq = RedisQueue(c.get(worker_section, "fanout_status_queue"), "fanout_broker_%s" % worker_number,
                  db=c.get(redis_section, "db"), 
                  host=c.get(redis_section, "host"), 
                  port=c.get(redis_section, "port")
                  )
  fanout_queues = [x.strip() for x in c.get(worker_section, "fanout").split(",") if x]
    
  if c.has_option(worker_section, "idletime"):
    try:
      idletime = float(c.get(worker_section, "idletime"))
    except ValueError:
        idletime = 10
   
  while(True):
    line = rq.pop()
    if line:
      fanout_success = True
      if topushq:
        # if there are residual messages to send, restart with those:
        if len(topushq) == 0:
          # if the queue is empty, and this is a clean start
          for q in fanout_queues:
            topushq.push(q)
        # Distribution:
        while len(topushq) != 0:
          q = topushq.pop()
          rq.push(line, to_queue=q)
          topushq.task_complete()
          rq.task_complete()
      else:
        for q in fanout_queues:
          rq.push(line, to_queue=q)
        rq.task_complete()
    else:
      # ratelimit to stop it chewing through CPU cycles
      sleep(idletime)
