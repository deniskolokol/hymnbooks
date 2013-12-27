# encoding:utf-8 #

from mongoengine import connect, connection, register_connection
from mongoengine.context_managers import switch_db
from tastypie.test import ResourceTestCase
from mixer.backend.mongoengine import mixer
from django.conf import settings

from hymnbooks.apps.core import models, utils
from hymnbooks.apps.api import resources


# WARNING!
# Despite the hymnbooks.apps.core.tests.MongoTestRunner, and a proper creation
# of a test database, data is still being written to the default one - WHY??


def get_list_choices(deserialized_resp):
    """
    Returns choice list extracted from deserialized response.
    """
    return [item['id'] for item in deserialized_resp['objects']]


class MongoResourceTestCase(ResourceTestCase):
    """
    Tastypie ResourceTestCase modified for mongoengine.

    Warning! When testing MongoDB should be started without --auth option!
    """
    def setupUser(self, is_superuser=False, is_staff=False):
        self.user = mixer.blend(models.MongoUser,
                                is_superuser=is_superuser,
                                is_staff=is_staff)
        return self.user

    def get_credentials(self, user):
        auth_user = user if user else self.user
        return self.create_basic(username=auth_user.username,
                                 password=auth_user.password)

    def get_credentials_api_key(self, user=None):
        auth_user = user if user else self.user
        return self.create_apikey(username=auth_user.username,
                                  api_key=auth_user.api_key)        

class MongoResourcePermissionsTestCase(MongoResourceTestCase):
    """
    Mongoengine test case for resources that require permission.
    """
    auth_uri = '?username=%s&api_key=%s'

    def setUp(self):
        super(MongoResourcePermissionsTestCase, self).setUp()

        self.super_user = self.setupUser(is_superuser=True)
        self.staff_user = self.setupUser(is_staff=True)
        self.user = self.setupUser()


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
        self.user = self.setupUser(is_staff=True)
        _p = lambda m: [{"permission": p[0], "document_type": m} for p in models.PERMISSION_TYPE]
        self.post_data = [{"name": "Kabalyeros", "permissions": _p('Section')},
                          {"name": "Escuderos", "permissions": _p('Manuscript')}]
        self.uri_auth = '?username=%s&api_key=%s' % (self.user.username, self.user.api_key)

    def test_post_detail_unauthorized(self):
        self.assertHttpUnauthorized(self.api_client.post('/api/v1/admin_group/', format='json', data=self.post_data))

    # def test_post_detail_authorized(self):
    #     # Waring! This test doesn't pass even if the authorization working!
    #     # Solve it! See http://stackoverflow.com/questions/13028906/cant-do-post-with-curl-and-apikeyauthentication-in-tastypie
    #     resp = self.api_client.post('/api/v1/admin_group/%s' % self.uri_auth,
    #                                 data=self.post_data, format='json')
        
    #     self.assertHttpCreated(resp)

    def test_get_list(self):
        # Unauthenticated.
        resp = self.api_client.get('/api/v1/admin_group/', format='json')

        # Http response should be OK, but no data.
        self.assertHttpOK(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        # # Authenticated.
        # resp = self.api_client.get('/api/v1/admin_group/', format='json', authentication=self.get_credentials_api_key())
        # print self.deserialize(resp)
        # self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    # def test_get_group_list_authenticated(self):
    #     resp = self.api_client.get('/api/v1/admin_group/', format='json', authentication=self.get_credentials())
        
    #     # Http response should be OK.
    #     self.assertHttpOK(self.api_client.get('/api/v1/admin_group/', format='json'))

    #     # But no data.
    #     self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    # def test_patch_detail_unauthorzied(self):
    #     self.assertHttpUnauthorized(self.api_client.get('/api/v1/admin_group/', format='json'))
        
    # def test_patch_detail(self):
    #     # Freshly created group.
    #     with switch_db(models.MongoGroup, self.alias) as Group:
    #         new_group = Group.objects.latest('pk')

    #         # Prepare group data.
    #         self.patch_data = [{"permission": p[0], "document_type": "Manuscript"} for p in models.PERMISSION_TYPE]

    #         # Patch it.
    #         self.assertHttpCreated(self.api_client.post(
    #             '/api/admin_group/%s/permission/%s/' % (new_group, self.uri_auth), format='json', data=self.patch_data))

    #         # Check permissions!




    
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

class ManuscriptResourceTest(MongoResourcePermissionsTestCase):

    post_data = {
        "title": "Kancjonał St. M",
        "description": """
    Rękopis papierowy oprawny w okładkę papierową. Zawiera 25 kart numerowanych (numeracja ciągła) w formacie stojącym o wymiarach 214 x 180 mm, oraz kart nlb. stanowiących część okładki. Brak karty tytułowej. Rękopis datowany przez W. Świerczka na 2 poł. XVIII wieku. Na okładce w lewym górnym rogu biała kwadratowa naklejka z wpisanym niebieskim atramentem St 7 M | (XVIII w). Obok naklejka okrągła z wpisanym M. poniżej naklejkaprostokątna z granatową ramką, z wpisanym różowym atramentem Benedyktynk. | Staniątki | 71/XVIII w. Trzon rękopisu spisany jedną ręką (zapis nutowy wraz tekstem słownym).
    """
        }
    patch_data_status = {"status": "active"}
    patch_data_content = {}
    patch_data_piece = {}
    patch_data_media = {}

    def setUp(self):
        super(ManuscriptResourceTest, self).setUp()

        self.resource_uri = resources.ManuscriptResource().get_resource_uri()

    def test_get_list(self):
        # Unauthenticated.        
        resp = self.api_client.get(self.resource_uri, format='json')

        # Http response should be OK, but no data.
        self.assertHttpOK(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def test_post_unauthorized(self):
        self.assertHttpUnauthorized(self.api_client.post(self.resource_uri,
                                                         format='json',
                                                         data=self.post_data))

    def test_post_authorized(self):
        
        self.resource_uri += self.auth_uri % (self.super_user.username,
                                              self.super_user.api_key)
        resp = self.api_client.post(self.resource_uri,
                                    format='json',
                                    data=self.post_data)

        # Http response should be OK.
        # BUT IT ISN'T! WHY??!!
        self.assertHttpOK(resp)

        # One document should be inserted.
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        # Check creation of:
        # - name
        # - created and created_by
