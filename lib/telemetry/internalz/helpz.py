from projects.lib.telemetry.internalz import handlers


def HandleHelpz(environ, start_response):
  start_response('200 OK', [('Content-Type', 'text/html')])
  yield '<html><body>'
  yield '<h2>Registered paths:</h2>'
  for path in handlers.AllHandlers():
    yield '<a href="%s">%s</a><br>' % (path, path)
  yield '</body></html>'

handlers.RegisterHandler('/helpz', HandleHelpz)
