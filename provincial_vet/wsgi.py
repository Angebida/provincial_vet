"""
WSGI config for provincial_vet project.
"""
import os
import sys

# Update this path to your actual PythonAnywhere username
project_path = '/home/your_pythonanywhere_username/provincial_vet'
if project_path not in sys.path:
    sys.path.append(project_path)

from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'provincial_vet.settings')
application = get_wsgi_application()
