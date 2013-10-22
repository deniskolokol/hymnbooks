# encoding:utf-8 #

from mongoengine import connect, connection
from mongoengine.context_managers import switch_db

from tastypie.test import ResourceTestCase
from tastypie_mongoengine.test_runner import MongoEngineTestCase

from mixer.backend.mongoengine import mixer

from hymnbooks.apps.core import models

from django.conf import settings

import random
import string


def get_list_choices(deserialized_resp):
    """
    Returns choice list extracted from deserialized response.
    """
    return [item['id'] for item in deserialized_resp['objects']]

def id_generator(size=6, chars=string.ascii_lowercase+string.digits):
    """
    Generates quazi-unique sequence from random digits and letters.
    """
    return ''.join(random.choice(chars) for x in range(size))


class MongoResourceTestCase(ResourceTestCase):
    """
    Tastypie ResourceTestCase modified for mongoengine. Clears the collection
    between the tests.

    Warning! When testing mongo should be started without --auth option!
    """
    alias = 'test_db'
    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    username = 'test_user'
    password = 'test_password'
    user_email = 'test@localhost.local'

    def _pre_setup(self):
        connection.disconnect() # from the current db
        db_opts = dict((k, v) for k, v 
                       in settings.MONGO_DATABASE_OPTIONS.iteritems() 
                       if k in ['host', 'port'])
        connect(self.db_name, self.alias, **db_opts)

        super(MongoResourceTestCase, self)._pre_setup()

    def _post_teardown(self):
        current_connection = connection.get_connection(alias=self.alias)
        current_connection.drop_database(self.db_name)
        current_connection.disconnect()

        super(MongoResourceTestCase, self)._post_teardown()


    def setupUser(self, is_staff=False):
        with switch_db(models.MongoUser, self.alias) as User:
            self.user = mixer.blend(User,
                                    password=id_generator(),
                                    email='%s@localhost.local' % id_generator(),
                                    is_staff=is_staff)
            # self.user.save()

        return self.user


class APITopLevelTest(ResourceTestCase):
    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/', format='json')

        self.assertValidJSONResponse(resp)


class PermissionResourceTest(ResourceTestCase):

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/permission/', format='json')

        self.assertValidJSONResponse(resp)

        # Is there proper number of elements?
        self.assertEqual(len(self.deserialize(resp)['objects']), len(models.PERMISSION_TYPE))

        # Are keys correct?
        self.assertEqual(get_list_choices(self.deserialize(resp)), dict(models.PERMISSION_TYPE).keys())

    def test_get_detail_json(self):
        # Detail view not allowed.
        self.assertHttpMethodNotAllowed(self.api_client.get('/api/v1/permission/read_list/', format='json'))


class DocumentTypeResourceTest(ResourceTestCase):

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/document_type/', format='json')

        self.assertValidJSONResponse(resp)

        # Is there proper number of elements?
        self.assertEqual(len(self.deserialize(resp)['objects']), len(models.DOCUMENT_TYPE))

        # Are keys correct?
        self.assertEqual(get_list_choices(self.deserialize(resp)), dict(models.DOCUMENT_TYPE).keys())

    def test_get_detail_json(self):
        # Detail view not allowed.
        self.assertHttpMethodNotAllowed(self.api_client.get('/api/v1/document_type/MongoUserProfile/', format='json'))


class FieldTypeResourceTest(ResourceTestCase):

    def test_get_list_json(self):
        resp = self.api_client.get('/api/v1/field_type/', format='json')

        self.assertValidJSONResponse(resp)

        # Is there right number of field_types?
        self.assertEqual(len(self.deserialize(resp)['objects']), len(models.FIELD_TYPE))

        # Are keys correct?
        self.assertEqual(get_list_choices(self.deserialize(resp)), dict(models.FIELD_TYPE).keys())

    def test_get_detail_json(self):
        # Detail view not allowed.
        self.assertHttpMethodNotAllowed(self.api_client.get('/api/v1/field_type/embeddeddocument/', format='json'))


class GroupResourceTest(MongoResourceTestCase):
    def setUp(self):
        super(GroupResourceTest, self).setUp()

        self.user = super(GroupResourceTest, self).setupUser(is_staff=True)

        self.uri_auth = '?username=%s&api_key=%s' % (self.user.username, self.user.api_key)

    def test_get_section_list(self):
        # Http response should be OK, but no data.
        self.assertHttpOK(self.api_client.get('/api/v1/admin_group/', format='json'))

    def post_detail(self):
        # Generate permission data for document_type.
        self.post_data = {"name": "Moderators",
                          "permissions": [{"permission": p[0], "document_type": "Section"}
                                          for p in models.PERMISSION_TYPE]}
        self.assertHttpCreated(self.api_client.post('/api/admin_group/%s' % self.uri_auth, format='json', data=self.post_data))

        # Check permissions!

    def patch_detail(self):
        # Freshly created group.
        with switch_db(models.MongoGroup, self.alias) as Group:
            new_group = Group.objects.latest('pk')

            # Prepare group data.
            self.patch_data = [{"permission": p[0], "document_type": "Manuscript"} for p in models.PERMISSION_TYPE]

            # Patch it.
            self.assertHttpCreated(self.api_client.post(
                '/api/admin_group/%s/permission/%s/' % (new_group, self.uri_auth), format='json', data=self.patch_data))

            # Check permissions!

    def patch_detail(self):
        # Freshly created group.
        with switch_db(models.MongoGroup, self.alias) as Group:
            new_group = Group.objects.latest('pk')

            # Prepare group data.
            self.patch_data = [{"permission": p[0], "document_type": "Manuscript"} for p in models.PERMISSION_TYPE]

            # Patch it.
            self.assertHttpCreated(self.api_client.post(
                '/api/admin_group/%s/permission/%s/' % (new_group, self.uri_auth), format='json', data=self.patch_data))

            # Check permissions!
        
# class SectionResourceTest(MongoResourceTestCase):
#     def setUp(self):
#         super(SectionResourceTest, self).setUp()

#         self.user = super(SectionResourceTest, self).setupUser()

#         self.uri_auth = '?username=%s&api_key=%s' % (self.user.username,
#                                                      self.user.api_key)
#         self.post_data = {
#             "title" : "support",
#             "help_text" : "Wsparcie",
#             "fields" : {
#                 "evidence" : {
#                     "blank": "true",
#                     "default": "null",
#                     "help_text": "Dowód",
#                     "nullable": "true",
#                     "readonly": "false",
#                     "type": "string",
#                     "unique": "false"
#                     },
#                 "source" :  {
#                     "blank": "true",
#                     "default": "null",
#                     "help_text": "Źródło",
#                     "nullable": "true",
#                     "readonly": "false",
#                     "type": "string",
#                     "unique": "false"
#                     },
#                 "trusted" :  {
#                     "blank": "true",
#                     "default": "true",
#                     "help_text": "Potwierdzone",
#                     "nullable": "false",
#                     "readonly": "false",
#                     "type": "boolean",
#                     "unique": "false"
#                     }
#                 }
#             }        

#     def test_get_section_list(self):
#         # Http response should be OK, but no data.
#         self.assertHttpOK(self.api_client.get('/api/v1/section/', format='json'))
