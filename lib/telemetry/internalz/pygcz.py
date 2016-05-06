import cgi
import gc
import sys
import urlparse


def HandlePygcz(environ, start_response):
  total_size = 0
  object_sizes = {}
  object_counts = {}

  objects = gc.get_objects()
  for obj in objects:
    obj_size = sys.getsizeof(obj)
    obj_type = str(type(obj))

    total_size += obj_size
    object_sizes[obj_type] = object_sizes.get(obj_type, 0) + obj_size
    object_counts[obj_type] = object_counts.get(obj_type, 0) + 1

  qs = urlparse.parse_qs(environ['QUERY_STRING'], keep_blank_values=True)
  sort_by = qs.get('sort', ['obj'])[0]
  if sort_by not in ['obj', 'count', 'size']:
    sort_by = 'obj'
  sort_reverse = 'reverse' in qs

  if sort_by == 'obj' and not sort_reverse:
    sort_obj = 'sort=obj&reverse'
  else:
    sort_obj = 'sort=obj'
  if sort_by == 'count' and not sort_reverse:
    sort_count = 'sort=count&reverse'
  else:
    sort_count = 'sort=count'
  if sort_by == 'size' and not sort_reverse:
    sort_size = 'sort=size&reverse'
  else:
    sort_size = 'sort=size'

  response = ['<html><body>']
  response.append(
      '<pre>%d objects\n%d bytes total</pre><br>' % (len(objects), total_size))
  response.append('<table>')
  response.append('<tr>')
  response.append(
      '<th><a href="?%s"><pre>Object</pre></a></th>' % (sort_obj,))
  response.append(
      '<th><a href="?%s"><pre>Count</pre></a></th>' % (sort_count,))
  response.append(
      '<th><a href="?%s"><pre>Total Size</pre></a></th>' % (sort_size,))
  response.append('</tr>')

  if sort_by == 'count':
    sorted_keys = sorted(
        object_counts, key=lambda x: object_counts[x], reverse=sort_reverse)
  elif sort_by == 'size':
    sorted_keys = sorted(
        object_sizes, key= lambda x: object_sizes[x], reverse=sort_reverse)
  else:
    sorted_keys = sorted(object_sizes.keys(), reverse=sort_reverse)

  for obj in sorted_keys:
    response.append('<tr>')
    response.append('<td><pre>%s</pre></td>' % (cgi.escape(obj),))
    response.append('<td style="padding: 0 30px;"><pre>%s</pre></td>' % (object_counts[obj],))
    response.append('<td style="padding: 0 30px;"><pre>%s</pre></td>' % (object_sizes[obj],))
    response.append('</tr>')
  response.append('</table></body></html>')

  start_response('200 OK', [('Content-Type', 'text/html')])
  return ''.join(response)
