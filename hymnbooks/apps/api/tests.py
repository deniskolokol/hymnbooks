# encoding:utf-8 #

from mongoengine import connect, connection
from tastypie.test import ResourceTestCase
from mongoengine.django.auth import User
from tastypie_mongoengine.test_runner import MongoEngineTestCase

from hymnbooks.apps import core, api


class FieldTypeResourceTest(ResourceTestCase):

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/field_type/',
                                   format='json')
        # WARNING! When using Authentication, add kwarg:
        # authentication=self.get_credentials()

        self.assertValidJSONResponse(resp)

        # Is there right number of field_types?
        self.assertEqual(len(self.deserialize(resp)['objects']),
                         len(core.models.FIELD_TYPE))

        # Are there correct field_type keys?
        field_types = [item['id'] for item in self.deserialize(resp)['objects']]
        self.assertEqual(field_types, dict(core.models.FIELD_TYPE).keys())

    def test_get_detail_json(self):
        # Detail view not allowed.
        self.assertHttpMethodNotAllowed(
            self.api_client.get('/api/v1/field_type/detail/', format='json'))


# WARNING! Find workaround to import data from fixtures!
class ManuscriptResourceTest(ResourceTestCase):
    fixtures = ['manuscript_resource_test.json']

    def setUp(self):
        super(ManuscriptResourceTest, self).setUp()

        # Create a user.
        self.username = 'test_user'
        self.password = 'testuserpass'
        self.user = User.objects.create_user(self.username, 'daniel@example.com', self.password)

        # ...
