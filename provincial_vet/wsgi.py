"""
WSGI config for provincial_vet project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'provincial_vet.settings')
application = get_wsgi_application()
