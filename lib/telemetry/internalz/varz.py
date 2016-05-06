from projects.lib.telemetry import event_collection


def HandleVarz(environ, start_response):
  events = event_collection.GetEvents()
  response = []
  for k in sorted(events.keys()):
    response.append('%s %r' % (k, events[k]))
  start_response('200 OK', [('Content-Type', 'text/plain')])
  return '\n'.join(response)
