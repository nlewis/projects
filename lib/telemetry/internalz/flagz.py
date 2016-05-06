import gflags

def HandleFlagz(environ, start_response):
  start_response('200 OK', [('Content-Type', 'text/plain')])

#  return gflags.FLAGS.FlagsIntoString()

  for flag in gflags.FLAGS.FlagDict().values():
    if flag.value is None:
      yield '--no%s' % (flag.name,)
    else:
      yield flag.Serialize()
    yield '\n'

#  for flag_name, flag_value in gflags.FLAGS.FlagValuesDict().iteritems():
#    if flag_value in [None, False]:
#      yield '--no%s\n' % (flag_name,)
#    else:
#      yield '--%s=%s\n' % (flag_name, flag_value)
