#!/usr/bin/env python

import os
import sys
import json
import requests
import gevent
import gevent.monkey
import gevent.pool

gevent.monkey.patch_all(thread=False, select=False)

from settings import api_keys, host

request_lines = []

def get_data(line, method, url, api_key):
  global request_lines

  response = requests.get(url)
  if response.status_code < 400:
    data = json.loads(response.text)
    data.pop('attachments', None)
    data.pop('submissions', None)
    data.pop('updated_datetime', None)
    data.pop('created_datetime', None)
    data.pop('dataset', None)
    data.pop('place', None)
    data.pop('id', None)
    data.pop('url', None)
    data['test_data'] = True
    data = json.dumps(data)
    request_lines.append(make_line(method, url, data, api_key))
  else:
    raise Exception('Problem with line: %s\n%s %s' % (line, response.status_code, response.text))

def make_line(method, url, data, api_key):
  return "log_requests.request(%r, %r, data=%r, headers={'X-Shareabouts-key': %r, 'content-type': 'application/json'})" % (method, url, data, api_key)

def main():
  global request_lines, host
  infile = sys.stdin

  print '#!/usr/bin/env python'
  print '#-*- coding:utf-8 -*-'
  print
  print 'import sys'
  print 'import log_requests'
  print

  request_jobs = []
  pool = gevent.pool.Pool(50)

  for line in infile:
    method, path = line.strip().split(' ', 1)

    # Make old-style paths into new ones
    dirs = path.split('/')
    if dirs[3] == 'datasets':
        dirs[3], dirs[4] = dirs[4], dirs[3]
        path = '/'.join(dirs)

    owner, _, dataset = path.split('/')[3:6]
    api_key = api_keys['/'.join([owner, dataset])]

    if method.lower() == 'put':
      request_jobs.append(pool.spawn(get_data, line, method, host + path, api_key))
    elif method.lower() == 'post':
      data = json.dumps({'location': {'lat': 1, 'lng': 1}, 'test_data': True})
      request_lines.append(make_line(method, host + path, data, api_key))
    else:
      data = ''
      request_lines.append(make_line(method, host + path, data, api_key))

  gevent.joinall(request_jobs)
  print '\n'.join(request_lines)
  print
  print "if __name__ == '__main__':"
  print "  log_requests.send_requests(int(sys.argv[1]))"



if __name__ == '__main__':
  sys.exit(main())
