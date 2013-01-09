#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys

def main():
  infile = sys.stdin

  for line in infile:
    try:
      subline = line
      subline = subline.split('"')[1]
      subline = subline.split('HTTP')[0].strip()
      method, path = subline.split(' ', 1)
      if path.startswith('/api'):
        api_call = subline
        print api_call
    except:
      print 'ERROR', line
      raise

if __name__ == '__main__':
  sys.exit(main())
