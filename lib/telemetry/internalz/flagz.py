import gflags

def HandleFlagz(environ, start_response):
  start_response('200 OK', [('Content-Type', 'text/plain')])

  flags_long = set(gflags.FLAGS.FlagDict().values())
  for flag in sorted(flags_long):
    if flag.value is None:
      yield '--no%s' % (flag.name,)
    else:
      yield flag.Serialize()
    yield '\n'

