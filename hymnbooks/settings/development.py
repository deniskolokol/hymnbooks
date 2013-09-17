# Development settings for hymnbooks project.

import os.path
from hymnbooks.settings.base import *

# Go one level up from settings for the prohject root.
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(ROOT_PATH, 'site_media/')
MEDIA_URL = 'http://localhost:8000/site_media/'

STATIC_ROOT = os.path.join(ROOT_PATH, 'static/')
STATIC_URL = 'http://localhost:8000/static/'

STATICFILES_DIRS = ()

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates/'),
    os.path.join(ROOT_PATH, 'templates/cms/'),
    )
