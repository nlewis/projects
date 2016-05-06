#!/usr/bin/python -B

import os
import threading
import time
from projects.lib.concurrency import threadlib


class T1(threadlib.Thread):
  done = False
  def run(self):
    time.sleep(0.5)
    print 'self.tid from thread run(): %r' % (self.tid,)
    while not self.done:
      time.sleep(1)


def DumpThreads():
  for t in threading.enumerate():
    tid = getattr(t, 'tid', None)
    print '%s  pid: %s  tid: %s' % (t.name, os.getpid(), tid)


def main():
  DumpThreads()

  t1 = T1()
  t1.daemon = True
  t1.start()

  DumpThreads()

  time.sleep(1)
  t1.done = True
  t1.join()


if __name__ == '__main__':
  main()
