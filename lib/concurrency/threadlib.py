import ctypes
import platform
import sys
import threading

_SYS_GETTID_NR = None
_SYS_GETTID = {
    'x86_32': 224,
    'x86_64': 186,
}


def GetTid():
  # Not only does Python not have a built-in way to get a thread ID, glibc does
  # not provide a wrapper for the gettid system call; the syscall must be made
  # manually.
  global _SYS_GETTID_NR
  if _SYS_GETTID_NR is None:
    if platform.system() != 'Linux':
      return None

    if platform.machine() not in ['x86_64', 'i686']:
      return None

    if sys.maxsize > 2**32:
      _SYS_GETTID_NR = _SYS_GETTID['x86_64']
    else:
      _SYS_GETTID_NR = _SYS_GETTID['x86_32']

  return ctypes.pythonapi.syscall(_SYS_GETTID_NR)


class Thread(threading.Thread):
  """A subclass of threading.Thread with more instrumentation."""
  def __init__(self, *args, **kwargs):
    super(Thread, self).__init__(*args, **kwargs)
    self.tid = None

  def _set_ident(self, *args, **kwargs):
    super(Thread, self)._set_ident(*args, **kwargs)
    self.tid = GetTid()
    self.SetOSThreadName(self.name)

  def SetOSThreadName(self, name):
    if self.tid is None:
      return
    with open('/proc/self/task/%d/comm' % (self.tid,), 'w') as f:
      f.write(name)


# Set tid on MainThread.
threading.current_thread().tid = GetTid()
