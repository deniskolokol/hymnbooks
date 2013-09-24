# encoding:utf-8 #

from mongoengine import connect, connection
from tastypie.test import ResourceTestCase
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

        # Are there correct field types?
        field_types = [item['id'] for item in self.deserialize(resp)['objects']]
        self.assertEqual(field_types, dict(core.models.FIELD_TYPE).keys())

    # def test_get_detail_json(self):
    #     self.assertHttpApplicationError(
    #         self.api_client.get('/api/v1/field_type/detail/', format='json')
    #         )
