import sys
import threading
import traceback

from projects.lib.system import procfs


def HandleThreadz(environ, start_response):
  # --- Thread 7fdb37281371231 (name: worker_whatever) (daemon: True) stack: ---
  #   File "foo/blah.py", line 12, in DoSomething
  #   File "foo/meow.py", line 381, in MakeAThing
  #
  # --or--
  #
  # [FoThread, active, normal, tid=123456, age=28371.8s, cpu=242 (utime=200, stime=42), rate=0.00/s]
  #   File "whatever.py", line 11, in Whatever
  response = []

  process_stat = procfs.Stat()
  process_cpu_utime = process_stat['utime']
  process_cpu_stime = process_stat['stime']
  process_cpu_total = process_cpu_utime + process_cpu_stime

  for thread in threading.enumerate():
    state_str = 'alive' if thread.is_alive() else 'dead'
    kind_str = 'daemon' if thread.daemon else 'user'
    ident_str = 'ident=%s' % (hex(thread.ident),)
    tid = getattr(thread, 'tid', None)
    tid_str = 'tid=%s' % (tid,)

    if tid is not None:
      uptime = procfs.ProcessUptime(tid=tid)
    else:
      uptime = procfs.ProcessUptime(pid=pid)
    age_str = 'age=%.1fs' % (uptime,)

    stat = procfs.Stat(tid=tid)
    cpu_utime = stat['utime']
    cpu_stime = stat['stime']
    cpu_total = cpu_utime + cpu_stime

    if uptime:
      cpu_rate = cpu_total / uptime
    else:
      cpu_rate = 0

    if process_cpu_total:
      cpu_pct_of_total = 100 * cpu_total / process_cpu_total
    else:
      cpu_pct_of_total = 0

    line = []
    line.append('[%s' % (thread.name,))
    line.append(state_str)
    line.append(kind_str)
    line.append(ident_str)
    line.append(tid_str)
    line.append(age_str)
    line.append('cpu=%d' % (cpu_total,))
    line.append('(utime=%d' % (cpu_utime,))
    line.append('stime=%d)' % (cpu_stime,))
    line.append('rate=%0.2f/s' % (cpu_rate,))
    line.append('of_total=%0.2f%%]' % (cpu_pct_of_total,))

    response.append(', '.join(line))

    stack_trace = traceback.format_stack(sys._current_frames()[thread.ident])
    response.append('\t'.join(reversed(stack_trace)))

  start_response('200 OK', [('Content-Type', 'text/plain')])
  for line in response:
    yield line
    yield '\n'
