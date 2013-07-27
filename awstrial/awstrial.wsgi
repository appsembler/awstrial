import os
import sys

# We need to import lazr.restful first to work around a bug in the lazr.*
# namespace package.  If you do not import lazr.restful first then all
# imports of lazr.uri will fail.
import lazr.restful

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../sourcecode/django/'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../sourcecode/'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
