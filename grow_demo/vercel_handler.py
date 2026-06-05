import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grow_demo.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
