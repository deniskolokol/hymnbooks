from mongoengine.django.auth import User
from mongoengine import signals

from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.models import create_api_key
from tastypie.authorization import Authorization
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication
from tastypie_mongoengine.fields import *
from tastypie_mongoengine.resources import MongoEngineResource

from hymnbooks.apps.core import models, utils

DATE_FILTERS = ('exact', 'lt', 'lte', 'gte', 'gt',)

# Auto create API keys when user is saved.
signals.post_save.connect(create_api_key, sender=models.MongoUser)

class CustomApiKeyAuthentication(ApiKeyAuthentication):
    """
    Authenticates everyone if the request is GET otherwise performs
    ApiKeyAuthentication.
    """
    def is_authenticated(self, request, **kwargs):
        if request.method == 'GET':
            return True
        return super(CustomApiKeyAuthentication, self).is_authenticated(request, **kwargs)

    def get_identifier(self, request):
        return request.user.username

    
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
        # authentication = BasicAuthentication()

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

class FieldDefinitionResource(MongoEngineResource):
    class Meta:
        object_class = models.FieldDefinition
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        authorization = Authorization()
        authentication = BasicAuthentication()


class SectionResource(MongoEngineResource):
    fields = EmbeddedListField(
        of='hymnbooks.apps.api.resources.FieldDefinitionResource',
        attribute='fields', full=True, null=True)

    class Meta:
        object_class = models.Section
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        filtering = {
            'status': ALL,
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        authorization = Authorization()
        authentication = CustomApiKeyAuthentication()
        # authentication = BasicAuthentication()

    def hydrate(self, bundle):
        # Fill out `title` if not given
        if 'title' not in bundle.data:
            bundle.data['title'] = None
        if (bundle.data['title'] is None) or (
                bundle.data['title'].strip() == ''):
            try:
                bundle.data['title'] = utils.slugify_downcode(
                    bundle.data['help_text'])
            except:
                pass
        return bundle


class ManuscriptContentResource(MongoEngineResource):
    class Meta:
        resource_name = 'manuscript_content'
        object_class = models.ManuscriptContent
        allowed_methods = ('get', 'post')
        authorization = Authorization()
        # authentication = BasicAuthentication()


class PieceResource(MongoEngineResource):
    class Meta:
        object_class = models.Piece
        allowed_methods = ('get', 'post')
        authorization = Authorization()
        # authentication = BasicAuthentication()

        
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
        queryset = models.Manuscript.objects.all()
        # # WARNING! Specify allowed_methods after switching on Authorization and Authentication
        # allowed_methods = ('get', 'post', 'put', 'delete')
        # list_allowed_methods = ('get',)
        # detail_allowed_methods = ('get', 'post')
        allowed_methods = ('get', 'post')
        filtering = {
            'status': ALL,
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        authorization = Authorization()
        # authentication = BasicAuthentication()
