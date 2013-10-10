from mongoengine.django.auth import User, Group

from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie_mongoengine.fields import *
from tastypie_mongoengine.resources import MongoEngineResource

from hymnbooks.apps.core import models, utils
from hymnbooks.apps.api.auth import AppApiKeyAuthentication, AppAuthorization


DATE_FILTERS = ('exact', 'lt', 'lte', 'gte', 'gt', 'ne')

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
            # Resource will throw appropriate exception.
            pass
    return data

    
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
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()

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
        excludes = ('api_key', 'api_key_created', 'email', # WARNING! Re-write it when AppAuthorization is ready
                    'is_staff', 'is_superuser', 'password',) # (admins should see all fields!)
        filtering = {
            'is_active': ('exact', 'ne'),
            'date_joined': DATE_FILTERS
            }
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()


class GroupResource(MongoEngineResource):
    class Meta:
        object_class = Group
        allowed_methods = ('get')
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()    


class FieldDefinitionResource(MongoEngineResource):
    embedded_section = ReferenceField(
        to='hymnbooks.apps.api.resources.SectionResource',
        attribute='embedded_section', full=True, null=True)
    
    class Meta:
        object_class = models.FieldDefinition
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()

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
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'title', 'help_text',
                                  self.Meta.object_class)
        return bundle


class ManuscriptContentResource(MongoEngineResource):
    class Meta:
        resource_name = 'manuscript_content'
        object_class = models.ManuscriptContent
        allowed_methods = ('get', 'post')
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()


class PieceResource(MongoEngineResource):
    class Meta:
        object_class = models.Piece
        allowed_methods = ('get', 'post')
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()

        
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
        allowed_methods = ('get', 'post', 'patch', 'delete')
        filtering = {
            'status': ALL,
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        authorization = AppAuthorization()
        authentication = AppApiKeyAuthentication()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'slug', 'title',
                                  self.Meta.object_class)
        return bundle
