import functools
import gflags
import Queue
import sys
import threading
import time

from projects.lib.base import debuglog
from projects.lib.concurrency import threadlib
from projects.lib.telemetry import event_collection


FLAGS = gflags.FLAGS

gflags.DEFINE_integer('threadpool_numthreads', 4, 'Number of threads.',
                      lower_bound=1)


class ThreadPool(object):
  def __init__(self, size=None):
    if size is None:
      size = FLAGS.threadpool_numthreads

    self._size = size
    self._busy = []
    self._free = []
    self._sem = threading.Semaphore(self._size)
    self._lock = threading.Lock()
    self._queue = Queue.Queue()
    self._CreateThreads()
    self._RegisterEventCallbacks()

  def _RegisterEventCallbacks(self):
    event_collection.AddCallback('executor-threads-busy', self.GetNumBusy)
    event_collection.AddCallback('executor-threads-free', self.GetNumFree)
    event_collection.AddCallback('executor-tasks-queued', self.GetNumQueued)

  def GetNumBusy(self):
    with self._lock:
      return len(self._busy)

  def GetNumFree(self):
    with self._lock:
      return len(self._free)

  def GetNumQueued(self):
    with self._lock:
      return self._queue.qsize()

  def _GetThreadFromPool(self):
    start = time.time()
    self._sem.acquire()
    wait_ms = int((time.time() - start) * 1000)
    event_collection.Add('executor-queue-wait-ms', wait_ms)
    with self._lock:
      if not self._free:
        return None
      thread = self._free.pop()
      self._busy.append(thread)

    return thread

  def _ReturnThreadToPool(self, thread):
    with self._lock:
      self._busy.remove(thread)
      self._free.append(thread)
    self._sem.release()

  def _RunTasksInThread(self):
    while True:
      task = self._queue.get()

      thread = self._GetThreadFromPool()
      thread.task = task
      thread.event.set()

  def _CreateThreads(self):
    debuglog.Log('Creating %d threads', self._size)
    event_collection.Set('executor-threads-total', self._size)
    for i in xrange(self._size):
      t = ExecutorThread()

      t.daemon = True
      t.name = 'ThreadPool_ExecutorThread'
      t.event = threading.Event()
      t.returncb = self._ReturnThreadToPool
      t.shutdown = False
      t.task = None
      t.start()

      self._free.append(t)

    self._manager = threadlib.Thread(target=self._RunTasksInThread)
    self._manager.daemon = True
    self._manager.name = 'ThreadPool_Manager'
    self._manager.start()

  def RunTask(self, closure, donecb):
    event_collection.Increment('executor-tasks-run')
    if closure is None or donecb is None:
      raise TypeError('closure and donecb must not be None')

    self._queue.put((closure, donecb))

  def Shutdown(self):
    with self._lock:
      all_threads = self._busy + self._free

    for thread in all_threads:
      thread.shutdown = True
      thread.event.set()


class ExecutorThread(threadlib.Thread):
  def __init__(self):
    super(ExecutorThread, self).__init__()

  def run(self):
    while True:
      self.event.wait()
      self.event.clear()

      if self.shutdown:
        return

      closure, donecb = self.task

      result = closure()
      donecb(result)
      self.returncb(self)

  def Name(self):
    return '%s/%s' % (self.name, self.tid)
