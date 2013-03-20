#!/usr/bin/env python
import os
import sys

from os.path import abspath, dirname, join, pardir

if __name__ == "__main__":
    # Include the old Django REST Framework from the libs path.  See the note
    # for commit 8a9c3078826 for more information.
    sys.path.append(abspath(join(dirname(__file__), pardir, 'libs', 'django-rest-framework-0.4')))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
