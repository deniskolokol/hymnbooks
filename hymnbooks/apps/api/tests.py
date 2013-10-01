# encoding:utf-8 #

from mongoengine import connect, connection
from mongoengine.django.auth import User

from tastypie.test import ResourceTestCase
from tastypie_mongoengine.test_runner import MongoEngineTestCase

from hymnbooks.apps.core import models

from django.conf import settings


class MongoResourceTestCase(ResourceTestCase):
    """
    Tastypie ResourceTestCase modified for mongoengine. Clears the collection
    between the tests.
    """
    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    username = 'test_user'
    password = 'test_password'
    user_email = 'test@localhost.local'

    def _pre_setup(self):
        connection.disconnect() # from the current db
        connection.connect(self.db_name, **settings.MONGO_DATABASE_OPTIONS)
        super(MongoResourceTestCase, self)._pre_setup()

    def _post_teardown(self):
        current_connection = connection.get_connection()
        current_connection.drop_database(self.db_name)
        connection.disconnect()

        super(MongoResourceTestCase, self)._post_teardown()

    def setupUser(self):
        self.user = models.MongoUser.create_user(self.username,
                                                 self.password,
                                                 self.user_email)
        self.user.first_name, self.user.last_name = 'John Doe'.split()
        self.user.save()
        return self.user


class FieldTypeResourceTest(ResourceTestCase):

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/field_type/',
                                   format='json')
        # WARNING! When using Authentication, add kwarg:
        # authentication=self.get_credentials()

        self.assertValidJSONResponse(resp)

        # Is there right number of field_types?
        self.assertEqual(len(self.deserialize(resp)['objects']),
                         len(models.FIELD_TYPE))

        # Are there correct field_type keys?
        field_types = [item['id'] for item in self.deserialize(resp)['objects']]
        self.assertEqual(field_types, dict(models.FIELD_TYPE).keys())

    def test_get_detail_json(self):
        # Detail view not allowed.
        self.assertHttpMethodNotAllowed(
            self.api_client.get('/api/v1/field_type/detail/', format='json'))


class SectionResourceTest(MongoResourceTestCase):
    # Warning! Use Mixer to generate data!
    fixtures = []

    def setUp(self):
        super(SectionResourceTest, self).setUp()

        self.user = super(SectionResourceTest, self).setupUser()

        self.uri_auth = '?username=%s&api_key=%s' % (self.user.username,
                                                     self.user.api_key)
        self.post_data = {
            "title" : "support",
            "help_text" : "Wsparcie",
            "fields" : {
                "evidence" : {
                    "blank": "true",
                    "default": "null",
                    "help_text": "Dowód",
                    "nullable": "true",
                    "readonly": "false",
                    "type": "string",
                    "unique": "false"
                    },
                "source" :  {
                    "blank": "true",
                    "default": "null",
                    "help_text": "Źródło",
                    "nullable": "true",
                    "readonly": "false",
                    "type": "string",
                    "unique": "false"
                    },
                "trusted" :  {
                    "blank": "true",
                    "default": "true",
                    "help_text": "Potwierdzone",
                    "nullable": "false",
                    "readonly": "false",
                    "type": "boolean",
                    "unique": "false"
                    }
                }
            }        

    def test_get_section_list(self):
        # Http response should be OK, but no data.
        self.assertHttpOK(self.api_client.get('/api/v1/section/', format='json'))
