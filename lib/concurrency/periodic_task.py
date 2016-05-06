import cgi
import threading
import time

from projects.lib.base import logging
from projects.lib.concurrency import threadlib
from projects.lib.telemetry import event_collection
from projects.lib.telemetry.internalz import handlers


_IN_SHUTDOWN = False
_TASKS = []
_TASKS_LOCK = threading.RLock()


class PeriodicTaskError(Exception):
  pass


class PeriodicTask(threadlib.Thread):
  """Periodically run a task in a separate thread.

  A task can run an arbitrary number of times, including once. If a task is to
  be run more than once, an interval must be specified by calling Every().

  The task is eligible to run after StartingNow() or one of the StartingAfter*
  methods is called. The time it takes a task to run is not included in the
  interval. In other words, if a PeriodicTask with interval 10 seconds is
  created and started at 0h00m00s, the second run will occur at 0h00m00s
  whether the task completed in 0.1 seconds or 9.9 seconds. Overruns are not
  currently handled, which is kind of a bummer.

  The initialization functions return a reference to the object instance and
  are designed to be chained. Note that the Starting* method must be called
  last.

  task = AddTask(closure)

  # Example 1:
  task.RunForever().Every(seconds=10).StartingNow()

  # Example 2:
  task.RunOnce().StartingAfter(seconds=30)

  # Example 3:
  ready = threading.Event()
  task.Runs(5).Every(minutes=1).StartingAfterEvent(ready)
  """

  def __init__(self, task, *args, **kwargs):
    super(PeriodicTask, self).__init__(*args, **kwargs)
    self._task = task
    self._lock = threading.Lock()
    self._cancel = threading.Event()
    self._ready = threading.Event()
    self._pause = threading.Event()
    self._next_run = None
    self._pause_limbo_time = None
    self._run_interval = None
    self._runs_remaining = None
    self._runs_total = 0
    self._start_at = None
    self._start_event = None
    self._started_at = None
    self._current_state = self._WaitForReady

  def run(self):
    while self._current_state is not None:
      next_state = self._current_state()
      if next_state != self._current_state:
        logging.debug('current_state: %s', _StateName(self._current_state))
        logging.debug('next_state: %s', _StateName(next_state))
      self._current_state = next_state

  def _WaitForReady(self):
    """Waits until PeriodicTask is fully initialized.

    A PeriodicTask is considered ready when StartingNow() or one of the
    StartingAfter* methods is called.

    """
    self._ready.wait()

    if self._runs_remaining is None:
      raise PeriodicTaskError('Number of runs not set.')

    if self._runs_remaining > 1 and self._run_interval is None:
      raise PeriodicTaskError('Run interval not set.')

    return self._WaitForStart

  def _WaitForStart(self):
    """Waits until the starting condition is met or the task is canceled."""
    if self._start_at:
      return self._WaitForStartTime
    elif self._start_event:
      return self._WaitForStartEvent
    else:
      raise PeriodicTaskError('No start condition to wait for.')

  def _WaitForStartTime(self):
    with self._lock:
      start_time_passed = time.time() > self._start_at

    if start_time_passed:
      self._started_at = time.time()
      self._next_run = time.time() + self._run_interval
      return self._WaitForInterval

    cancelled = self._cancel.wait(0.2)
    if cancelled:
      return
    else:
      return self._WaitForStartTime

  def _WaitForStartEvent(self):
    if self._start_event.is_set():
      self._started_at = time.time()
      self._next_run = time.time() + self._run_interval
      return self._WaitForInterval

    cancelled = self._cancel.wait(0.2)
    if cancelled:
      return
    else:
      return self._WaitForStartEvent

  def _WaitForInterval(self):
    if self._pause.wait(0.05):
      return self._WaitForUnpause

    if self._cancel.wait(0.05):
      return

    if time.time() > self._next_run:
      return self._RunTaskNow
    else:
      return self._WaitForInterval

  def _RunTaskNow(self):
    self._next_run = time.time() + self._run_interval
    self._runs_total += 1
    self._task()

    self._runs_remaining -= 1
    if self._runs_remaining:
      return self._WaitForInterval
    else:
      return

  def _WaitForUnpause(self):
    cancelled = self._cancel.wait(0.1)
    if cancelled:
      return

    if self._pause.is_set():
      time.sleep(0.1)
      return self._WaitForUnpause
    else:
      if self._pause_limbo_time:
        self._next_run = time.time() + self._pause_limbo_time
        self._pause_limbo_time = None
      return self._WaitForInterval

  def Pause(self):
    self._pause.set()

    if self._next_run is None:
      self._pause_limbo_time = self._run_interval
    else:
      self._pause_limbo_time = max(self._next_run - time.time(), 0)
    logging.debug('pause_limbo_time: %.2f', self._pause_limbo_time)

  def Unpause(self):
    self._pause.clear()

  def Cancel(self):
    logging.info(
        'Cancelling %s (%s)', self.name, _StateName(self._current_state))
    self._cancel.set()

  def Every(self, seconds=None, minutes=None, hours=None):
    with self._lock:
      self._run_interval = 0
      if seconds:
        self._run_interval += seconds
      if minutes:
        self._run_interval += minutes * 60
      if hours:
        self._run_interval += hours * 60 * 60
    return self

  def RunOnce(self):
    self._runs_remaining = 1
    return self

  def RunForever(self):
    self._runs_remaining = float('inf')
    return self

  def Runs(self, runs):
    self._runs_remaining = runs
    return self

  def StartingAfter(self, seconds=None, minutes=None, hours=None):
    with self._lock:
      self._start_at = time.time()
      if seconds:
        self._start_at += seconds
      if minutes:
        self._start_at += minutes * 60
      if hours:
        self._start_at += hours * 60 * 60
    self._ready.set()
    return self

  def StartingAt(self, when):
    raise NotImplementedError()

  def StartingNow(self):
    with self._lock:
      self._start_at = time.time()
    self._ready.set()
    return self

  def StartingAfterEvent(self, event):
    with self._lock:
      self._start_event = event
    self._ready.set()
    return self

  def GetStartConditionText(self):
    if self._started_at is not None:
      return 'Started at %s' % (time.ctime(self._started_at),)

    if self._start_event:
      logging.debug('%r', self._start_event)
      return 'Waiting for %r' % (self._start_event,)

    if self._start_at:
      return 'Waiting until %s' % (time.ctime(self._start_at),)

    return 'Not startable'


def _StateName(state):
  if state is None:
    return 'Dead'
  else:
    return state.__name__


def AddTask(closure):
  if _IN_SHUTDOWN:
    logging.warning('Attempted to add task while shutting down')
    return

  # Invariant: All tasks in _TASKS are alive.
  with _TASKS_LOCK:
    task = PeriodicTask(closure)
    task.daemon = True
    task.start()
    task.name = 'PeriodicTask/%d' % (task.tid)
    _TASKS.append(task)
  return task


def RemoveTask(task):
  # Invariant: All live tasks are in _TASKS.
  if not task._cancel.is_set():
    logging.warning('Task %s being removed while still alive', task.name)
    logging.warning('You should explicitly call task.Cancel()')
    task.Cancel()

  with _TASKS_LOCK:
    logging.info('Waiting for %s to terminate', task.name)
    task.join()
    _TASKS.remove(task)


def CancelAllTasks():
  with _TASKS_LOCK:
    # First, all tasks are cancelled, then all tasks are removed. Two stages
    # are used because RemoveTask() calls join() on the task, which can block
    # if the task is busy.
    for task in _TASKS:
      task.Cancel()

    # _TASKS is modified in this loop so we make a copy.
    for task in _TASKS[:]:
      RemoveTask(task)


def Shutdown():
  logging.info('Shutting down periodic tasks')
  with _TASKS_LOCK:
    _IN_SHUTDOWN = True
    CancelAllTasks()


def TasksTotal():
  with _TASKS_LOCK:
    return len(_TASKS)

def TasksStarted():
  with _TASKS_LOCK:
    return len([t for t in _TASKS if t._started_at is not None])

def HandleTaskz(environ, start_response):
  response = []
  response.append('<html><body><pre>')
  response.append('<p>Current time: %s</p>' % time.ctime(time.time()))
  response.append('<table style="border-spacing: 10px 2px;">')
  response.append('<tr>')
  response.append('<th>Task</th>')
  response.append('<th>Started</th>')
  response.append('<th>State</th>')
  response.append('<th>Paused</th>')
  response.append('<th>Next Run</th>')
  response.append('<th>Times Run</th>')
  response.append('<th>Runs Remaining</th>')
  response.append('</tr>')

  with _TASKS_LOCK:
    for task in _TASKS:
      response.append('<tr>')
      with task._lock:
        response.append('<td>%s</td>' % (task.name))
        response.append('<td>%s</td>' % (
            cgi.escape(task.GetStartConditionText()),))
        response.append('<td>%s</td>' % (task._current_state.__name__,))
        response.append('<td>%s</td>' % (task._pause.is_set(),))

        if task._next_run:
          next_run = time.ctime(task._next_run)
        else:
          next_run = 'Not started'
        response.append('<td>%s</td>' % (next_run,))
        response.append('<td>%s</td>' % (task._runs_total,))
        response.append('<td>%s</td>' % (task._runs_remaining,))
      response.append('</tr>')

  response.append('</table></pre></body></html>')

  start_response('200 OK', [('Content-Type', 'text/html')])
  for line in response:
    yield line


handlers.RegisterHandler('/taskz', HandleTaskz)

event_collection.AddCallback('periodic-tasks-total', TasksTotal)
event_collection.AddCallback('periodic-tasks-started', TasksStarted)
