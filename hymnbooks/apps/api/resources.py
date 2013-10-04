from mongoengine.django.auth import User
from mongoengine import signals

from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.models import create_api_key
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie_mongoengine.fields import *
from tastypie_mongoengine.resources import MongoEngineResource

from hymnbooks.apps.core import models, utils

DATE_FILTERS = ('exact', 'lt', 'lte', 'gte', 'gt', 'ne')

# Auto create API key when user is saved.
signals.post_save.connect(create_api_key, sender=models.MongoUser)

def ensure_slug(data, field, field_fro, obj_class=None):
    """
    Autofill slug-like field.
    Slugify unique, if obj_class (reference to appropriate model class).
    """
    if field not in data:
        data[field] = None
    if (data[field] is None) or (data[field].strip() == ''):
        try:
            data[field] = utils.slugify_unique(data[field_fro],
                                               obj_class,
                                               slugfield=field)
        except AttributeError:
            # Either `obj_class` not specified or it doesn't have `.objects`.
            data[field] = utils.slugify_downcode(data[field_fro])
        except:
            # In all other cases (like KeyError) simply leave data as is:
            # Resource will through appropriate exception.
            pass
    return data


class CustomApiKeyAuthentication(ApiKeyAuthentication):
    """
    Authenticates everyone if the request is GET otherwise performs
    ApiKeyAuthentication.
    """
    def is_mongouser_authenticated(self, request):
        """
        Custom solution for MongoUser ApiKey authentication.
        ApiKey here is not a class (as it is realized in ORM approach),
        but a field MongoUser class.
        """
        username, api_key = super(CustomApiKeyAuthentication,
                                  self).extract_credentials(request)
        try:
            models.MongoUser.objects.get(username=username, api_key=api_key)
        except models.MongoUser.DoesNotExist:
            return False

        return True
    
    def is_authenticated(self, request, **kwargs):
        """
        Custom solution for `is_authenticated` function: MongoUsers has got
        authenticated through custom api_key check.
        """
        if request.method == 'GET':
            return True
        try:
            is_authenticated = super(CustomApiKeyAuthentication,
                                     self).is_authenticated(request, **kwargs)
        except TypeError as e:
            if "MongoUser" in str(e):
                is_authenticated = self.is_mongouser_authenticated(request)
            else:
                is_authenticated = False
        return is_authenticated

    
class BaseCategory(object):
    """
    Container class for list of categories. Id and name only.
    """
    id = None
    name = None

    def __init__(self, *args, **kwargs):
        try:
            self.id, self.name = args
        except:
            self.id = kwargs.get('id', None)
            self.name = kwargs.get('name', None)


class FieldTypeResource(Resource):
    """
    Returns list of Field Types.

    Serves informational purposes. Neither POST/PUT/DELETE allowed, nor GET for
    detail (resource_uri key is absent). No filters either. The resource can be
    used to check correctness of category value when filling other resources.
    """
    id = fields.CharField(attribute='id')
    name = fields.CharField(attribute='name')

    class Meta:
        resource_name = 'field_type'
        list_allowed_methods = ('get',)
        detail_allowed_methods = ()
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()

    def get_object_list(self, request):
        """
        Populates Resource with data.
        """
        return [BaseCategory(id=k, name=v) for k, v in dict(models.FIELD_TYPE).iteritems()]

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    def dehydrate(self, bundle):
        """
        Final processing - get rid of resource_uri.
        """
        del bundle.data['resource_uri']
        return bundle

class MongoUserResource(MongoEngineResource):
    class Meta:
        resource_name = 'user'
        object_class = models.MongoUser
        allowed_methods = ('get')
        excludes = ('api_key', 'api_key_created', 'email', # WARNING! Re-write it when Authorization is ready
                    'is_staff', 'is_superuser', 'password',) # (admins should see all fields!)
        filtering = {
            'is_active': ('exact', 'ne'),
            'date_joined': DATE_FILTERS
            }
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()


class FieldDefinitionResource(MongoEngineResource):
    embedded_section = ReferenceField(
        to='hymnbooks.apps.api.resources.SectionResource',
        attribute='embedded_section', full=True, null=True)
    
    class Meta:
        object_class = models.FieldDefinition
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'field_name', 'help_text')
        if 'embedded_section' in bundle.data:
            bundle.data['field_type'] = 'embeddeddocument'
        return bundle


class SectionResource(MongoEngineResource):
    fields = EmbeddedListField(
        of='hymnbooks.apps.api.resources.FieldDefinitionResource',
        attribute='fields', full=True, null=True)

    class Meta:
        object_class = models.Section
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        filtering = {
            'status': ('exact', 'ne'),
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        always_return_data = True
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'title', 'help_text',
                                  self.Meta.object_class)
        return bundle


class ManuscriptContentResource(MongoEngineResource):
    class Meta:
        resource_name = 'manuscript_content'
        object_class = models.ManuscriptContent
        allowed_methods = ('get', 'post')
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()


class PieceResource(MongoEngineResource):
    class Meta:
        object_class = models.Piece
        allowed_methods = ('get', 'post')
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()

        
class ManuscriptResource(MongoEngineResource):
    """
    Manuscript data.
    """
    content = EmbeddedListField(
        of='hymnbooks.apps.api.resources.ManuscriptContentResource',
        attribute='content', full=True, null=True)
    pieces = EmbeddedListField(
        of='hymnbooks.apps.api.resources.PieceResource',
        attribute='pieces', full=True, null=True)
    
    class Meta:
        object_class = models.Manuscript
        # # WARNING! Specify allowed_methods after switching on Authorization and Authentication
        # allowed_methods = ('get', 'post', 'put', 'delete')
        # list_allowed_methods = ('get',)
        # detail_allowed_methods = ('get', 'post')
        allowed_methods = ('get', 'post', 'patch', 'delete')
        filtering = {
            'status': ALL,
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'slug', 'title',
                                  self.Meta.object_class)
        return bundle
