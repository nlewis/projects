def HandleSmapsz(environ, start_response):
  with open('/proc/self/smaps') as smaps:
    start_response('200 OK', [('Content-Type', 'text/plain')])
    for line in smaps:
      yield line
