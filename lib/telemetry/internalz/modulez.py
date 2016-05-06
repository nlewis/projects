import sys

def HandleModulez(environ, start_response):
  response = []
  response.append('<html><body><pre>')
  response.append('<table style="border-spacing: 10px 2px;">')
  response.append('<tr>')
  response.append('<th>Module</th>')
  response.append('<th>Path</th>')
  response.append('</tr>')

  for module_name in sorted(sys.modules):
    module = sys.modules[module_name]
    if module is None:
      continue
    module_path = getattr(module, '__file__', '(built-in)')
    response.append('<tr>')
    response.append('<td>%s</td>' % (module_name,))
    response.append('<td>%s</td>' % (module_path,))
    response.append('</tr>')

  response.append('</table></pre></body></html>')

  start_response('200 OK', [('Content-Type', 'text/html')])
  for line in response:
    yield line
