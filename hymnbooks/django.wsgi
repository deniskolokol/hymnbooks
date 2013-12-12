import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'hymnbooks.settings.development'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
