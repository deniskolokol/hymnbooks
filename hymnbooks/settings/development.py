# Development settings for hymnbooks project.

import os.path
from hymnbooks.settings.base import *

# Go one level up from settings for the project root.
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(ROOT_PATH, 'site_media/')

STATIC_ROOT = os.path.join(ROOT_PATH, 'static/')

STATICFILES_DIRS = ()

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates/'),
    os.path.join(ROOT_PATH, 'templates/cms/'),
    )

# Connect to the db.
from mongoengine import register_connection
register_connection('default', MONGO_DATABASE_NAME, **MONGO_DATABASE_OPTIONS)

TEST_RUNNER = 'hymnbooks.apps.core.tests.MongoTestRunner'
