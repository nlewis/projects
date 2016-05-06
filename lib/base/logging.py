import gflags
import inspect
import os
import threading
import time
import sys

from projects.lib.concurrency import threadlib


FLAGS = gflags.FLAGS

gflags.DEFINE_boolean(
    'verbose', False, 'Enable debug logging.', short_name='v')
gflags.DEFINE_boolean(
    'logtostderr', False, 'Log to stderr instead of to a file.')
gflags.DEFINE_boolean(
    'alsologtostderr', False, 'Log to stderr as well as to a file.')
gflags.DEFINE_string(
    'log_dir', '/var/log/projects', 'Directory where log files are written.')


LEVEL_FATAL = 0
LEVEL_ERROR = 1
LEVEL_WARNING = 2
LEVEL_INFO = 3
LEVEL_DEBUG = 4

_LOGLINE_PREFIX = ['F', 'E', 'W', 'I', 'D']

_INIT_LOCK = threading.Lock()

# Singleton.
_logger = None


def _DateAndTimeStr(when, date_fmt, time_fmt, usec=True):
  date_str = time.strftime(date_fmt, time.localtime(when))
  time_str = time.strftime(time_fmt, time.localtime(when))
  if usec:
    when_usec = '%d' % ((when - int(when)) * 1000000)
    return (date_str, '%s.%s' % (time_str, when_usec))
  else:
    return (date_str, time_str)


def _ProgramName():
  return os.path.basename(sys.modules['__main__'].__file__)


def _LogfileRealpath(logfile):
  return os.path.join(FLAGS.log_dir, logfile)


def _LogfileSympath(logfile):
  return os.path.join(FLAGS.log_dir, '%s.INFO' % (_ProgramName(),))


class Logger(object):
  def __init__(self):
    self.filename = self._NewFilename()
    self.realpath = _LogfileRealpath(self.filename)
    self.sympath = _LogfileSympath(self.filename)

    self.fds = []
    self._lock = threading.Lock()

  def _NewFilename(self):
    date_str, time_str = _DateAndTimeStr(time.time(), '%Y%m%d', '%H%M%S')
    filename = '%s.log.INFO.%s-%s.%s' % (
        _ProgramName(), date_str, time_str, os.getpid())
    return filename

  def _OpenLogFiles(self):
    # Lock so that in the future we can handle log rotation on-the-fly.
    with self._lock:
      for fd in self.fds:
        fd.close()

      self.fds = []

      if FLAGS.alsologtostderr or FLAGS.logtostderr:
        self.fds.append(sys.stderr)

      if not FLAGS.logtostderr:
        if not os.path.isdir(FLAGS.log_dir):
          os.mkdir(FLAGS.log_dir)

        self.fds.append(open(self.realpath, 'a'))

        if os.path.islink(self.sympath):
          os.unlink(self.sympath)
        os.symlink(self.realpath, self.sympath)

    create_date, create_time = _DateAndTimeStr(
        time.time(), '%Y/%m/%d', '%H:%M:%S')
    self._WriteRaw('Log file created at: %s %s\n' % (create_date, create_time))

  def _WriteRaw(self, line, flush=False):
    with self._lock:
      for fd in self.fds:
        fd.write(line)
        if flush:
          fd.flush()

  def Level(self):
    if FLAGS.verbose:
      return LEVEL_DEBUG
    else:
      return LEVEL_INFO

  def Log(self, level, msg, *args):
    if level > self.Level():
      return

    if not self.fds:
      self._OpenLogFiles()

    if not isinstance(msg, basestring):
      msg = str(msg)

    # TODO(nlewis): Handle log rotation.
    date_str, time_str = _DateAndTimeStr(time.time(), '%m%d', '%H:%M:%S')
    pid = '%6s' % (str(threadlib.GetTid()))
    caller_frame = inspect.stack()[2][0]
    caller_fn, caller_lineno, _, _, _ = inspect.getframeinfo(caller_frame)

    line = []
    line.append('%s%s ' % (_LOGLINE_PREFIX[level], date_str))
    line.append('%s ' % (time_str))
    line.append('%s ' % (pid))
    line.append('%s:%s] ' % (os.path.basename(caller_fn), caller_lineno))
    line.append(msg % args)
    line.append('\n')

    if level >= LEVEL_WARNING:
      flush = True
    else:
      flush = False

    self._WriteRaw(''.join(line), flush)


def debug(msg, *args):
  _logger.Log(LEVEL_DEBUG, msg, *args)


def info(msg, *args):
  _logger.Log(LEVEL_INFO, msg, *args)


def warning(msg, *args):
  _logger.Log(LEVEL_WARNING, msg, *args)


def error(msg, *args):
  _logger.Log(LEVEL_ERROR, msg, *args)


def fatal(msg, *args):
  _logger.Log(LEVEL_FATAL, msg, *args)
  sys.exit(1)


def _InitializeOnce():
  global _logger
  if _logger is not None:
    return
  _logger = Logger()


with _INIT_LOCK:
  _InitializeOnce()
