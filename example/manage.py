#!/usr/bin/env python
import imp
try:
    imp.find_module("settings")  # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write(
        "Error: Can't find the file 'settings.py' in the directory containing"
        "{0}. It appears you've customized things.\nYou'll have to run"
        "django-admin.py, passing it your settings module.\n".format(__file__))
    sys.exit(1)

from django.core.management import execute_manager

import settings


if __name__ == "__main__":
    execute_manager(settings)
