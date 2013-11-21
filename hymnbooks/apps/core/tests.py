from django.test.simple import DjangoTestSuiteRunner
from django.test import TestCase
from django.conf import settings

from mongoengine.connection import connect, disconnect, get_connection
from mongoengine import connect

class MongoTestRunner(DjangoTestSuiteRunner):
    """
    A test runner that can be used to create, connect to, disconnect from, 
    and destroy a mongo test database for standard django testing.
    
    NOTE:
    The MONGO_PORT and MONGO_DATABASE_NAME settings must exist, create them
    if necessary.

    REFERENCE:
    http://nubits.org/post/django-mongodb-mongoengine-testing-with-custom-test-runner/
    """

    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    host = settings.MONGO_DATABASE_OPTIONS['host']
    port = settings.MONGO_DATABASE_OPTIONS['port']

    def setup_databases(self, **kwargs):
        disconnect()
        connect(self.db_name, host=self.host, port=self.port)
        print 'Creating mongo test database ' + self.db_name

        return super(MongoTestRunner, self).setup_databases(**kwargs)
 
    def teardown_databases(self, old_config, **kwargs):
        connection = get_connection()
        connection.drop_database(self.db_name)
        print 'Dropping mongo test database: ' + self.db_name
        disconnect()

        super(MongoTestRunner, self).teardown_databases(old_config, **kwargs)
