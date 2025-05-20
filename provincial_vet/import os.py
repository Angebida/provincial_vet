import os
import sys

path = '/home/yourusername/provincial_vet'  # Replace with your project path
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'provincial_vet.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
