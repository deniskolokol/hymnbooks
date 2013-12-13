from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import Authentication, MultiAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie_mongoengine.resources import MongoEngineResource
from tastypie_mongoengine.fields import *

from hymnbooks.apps.core import models, utils
from hymnbooks.apps.api.auth import AppApiKeyAuthentication, CookieBasicAuthentication, \
     AnyoneCanViewAuthorization, StaffAuthorization, AppAuthorization


DATE_FILTERS = ('exact', 'lt', 'lte', 'gte', 'gt', 'ne')


def remove_duplicates(data):
    return dict((k, list(set(v))) if isinstance(v, list) else (k, v)
                for k, v in data.iteritems())


def hydrate_ref_list(obj, lst, field, action, uri):
    """
    Takes care of parameters with keywords (e.g. fieldname__append 
    or fieldname__delete).
    """
    uri_list = list()
    obj_list = getattr(obj, field)

    for element in obj_list:
        uri_list.append("%s%s/" % (uri, str(element.id)))

    if action == 'append':
        lst.extend(uri_list)
    elif action == 'delete':
        lst = [l for l in uri_list if l not in lst]

    return lst


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
        except:  # In all other cases (e.g. KeyError) leave data as is:
            pass # Resource will throw appropriate exception.
    return data

    
class BaseChoiceList(object):
    """
    Container class for list choice list. Id and name only.
    """
    id = None
    name = None

    def __init__(self, *args, **kwargs):
        try:
            self.id, self.name = args
        except:
            self.id = kwargs.get('id', None)
            self.name = kwargs.get('name', None)

    @classmethod
    def get_list(self, list_obj):
        return [self(id=k, name=v) for k, v in dict(list_obj).iteritems()]


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
        authorization = ReadOnlyAuthorization()
        authentication = Authentication()

    def obj_get_list(self, request=None, **kwargs):
        return BaseChoiceList.get_list(models.FIELD_TYPE)

    def dehydrate(self, bundle):
        del bundle.data['resource_uri']
        return bundle

class PermissionResource(Resource):
    """
    Returns list of Global Permissions. Serves informational purposes.
    """
    id = fields.CharField(attribute='id')
    name = fields.CharField(attribute='name')

    class Meta:
        resource_name = 'permission'
        list_allowed_methods = ('get',)
        detail_allowed_methods = ()
        authorization = ReadOnlyAuthorization()
        authentication = Authentication()

    def obj_get_list(self, request=None, **kwargs):
        return BaseChoiceList.get_list(models.PERMISSION_TYPE)

    def dehydrate(self, bundle):
        del bundle.data['resource_uri']
        return bundle

    
class DocumentTypeResource(Resource):
    """
    Returns list of Document types. Serves informational purposes.
    """
    id = fields.CharField(attribute='id')
    name = fields.CharField(attribute='name')

    class Meta:
        resource_name = 'document_type'
        list_allowed_methods = ('get',)
        detail_allowed_methods = ()
        authorization = ReadOnlyAuthorization()
        authentication = Authentication()

    def obj_get_list(self, request=None, **kwargs):
        return BaseChoiceList.get_list(models.DOCUMENT_TYPE)

    def dehydrate(self, bundle):
        del bundle.data['resource_uri']
        return bundle


class DocumentPermissionResource(MongoEngineResource):
    class Meta:
        object_class = models.GlobalPermission
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())
        authorization = StaffAuthorization()


class GroupResource(MongoEngineResource):
    permissions = EmbeddedListField(
        of='hymnbooks.apps.api.resources.DocumentPermissionResource',
        attribute='permissions', full=True, null=True)

    class Meta:
        object_class = models.MongoGroup
        resource_name = 'admin_group'
        excludes = ('id',)
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete',)
        authentication = MultiAuthentication(AppApiKeyAuthentication(), 
                                             CookieBasicAuthentication())
        authorization = StaffAuthorization()


class UserResource(MongoEngineResource):
    group = ReferencedListField(
        of='hymnbooks.apps.api.resources.GroupResource',
        attribute='group', full=True, null=True)
    permissions = EmbeddedListField(
        of='hymnbooks.apps.api.resources.DocumentPermissionResource',
        attribute='permissions', full=True, null=True)

    class Meta:
        resource_name = 'admin_user'
        object_class = models.MongoUser
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        # excludes = ('id', 'password',)
        filtering = {
            'username': ALL, # Filters are tuned to handle Authentication in the URL.
            'is_active': ('exact', 'ne'),
            'date_joined': DATE_FILTERS
            }
        authentication = MultiAuthentication(AppApiKeyAuthentication(), 
                                             CookieBasicAuthentication())
        authorization = StaffAuthorization()

    def hydrate(self, bundle):
        action_params = dict((k, v) for k, v in bundle.data.iteritems()
                             if '__' in k)
        if action_params:
            for param in action_params:
                field_name, field_action = param.split('__')
                field = getattr(self, field_name)
                ref_list = bundle.data.pop(param)
                related = field.get_related_resource(self)
                clean_list = hydrate_ref_list(obj=bundle.obj,
                                              lst=ref_list,
                                              field=field.attribute,
                                              action=field_action,
                                              uri=related.get_resource_uri())
                bundle.data[field_name] = clean_list

        # Remove duplicates.
        bundle.data = remove_duplicates(bundle.data)

        return bundle

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        # Eliminate `username` and `api_key` from filters.
        # Filter by username using `username__exact`.
        filters = dict((k, v) for k, v in filters.iteritems()
                       if k not in ['username', 'api_key'])

        orm_filters = super(UserResource, self).build_filters(filters)

        return orm_filters

class FieldDefinitionResource(MongoEngineResource):
    embedded_section = ReferenceField(attribute='embedded_section',
                                      to='hymnbooks.apps.api.resources.SectionResource',
                                      full=True, null=True)
    class Meta:
        object_class = models.FieldDefinition
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())
        authorization = AppAuthorization()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'field_name', 'help_text')
        if 'embedded_section' in bundle.data:
            bundle.data['field_type'] = 'embeddeddocument'
        return bundle

    
class EndUserDataResource(MongoEngineResource):
    created_by = ReferenceField(attribute='created_by',
                                to='hymnbooks.apps.api.resources.UserResource',
                                full=True)
    class Meta:
        authorization = AppAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

    def dehydrate(self, bundle):
        if bundle.request.method == 'GET':
            bundle.data['created_by_resource_uri'] = \
              '/api/v1/admin_user/%s/' % bundle.data['created_by'].obj.id
            bundle.data['created_by'] = \
              bundle.data['created_by'].obj.__unicode__()

        return bundle


class SectionResource(EndUserDataResource):
    fields = EmbeddedListField(attribute='fields',
                               of='hymnbooks.apps.api.resources.FieldDefinitionResource',
                               full=True, null=True)
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
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())
        authorization = AppAuthorization()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'title', 'help_text',
                                  self.Meta.object_class)
        return bundle


class ContentImageResource(EndUserDataResource):
    """
    Content Image data.
    """
    class Meta:
        resource_name = 'content_image'
        object_class = models.ContentImage
        allowed_methods = ('get', 'patch', 'delete')
        filtering = {
            'status': ALL,
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        authorization = AnyoneCanViewAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(), 
                                             CookieBasicAuthentication())


class ManuscriptContentResource(MongoEngineResource):
    class Meta:
        resource_name = 'manuscript_content'
        object_class = models.ManuscriptContent
        allowed_methods = ('get', 'post')
        authentication = MultiAuthentication(AppApiKeyAuthentication(), 
                                             CookieBasicAuthentication())
        authorization = AnyoneCanViewAuthorization()


class PieceResource(MongoEngineResource):
    class Meta:
        object_class = models.Piece
        allowed_methods = ('get', 'post')
        authentication = MultiAuthentication(AppApiKeyAuthentication(), 
                                             CookieBasicAuthentication())
        authorization = AnyoneCanViewAuthorization()

        
class ManuscriptResource(EndUserDataResource):
    """
    Manuscript data.
    """
    content = EmbeddedListField(attribute='content',
                                of='hymnbooks.apps.api.resources.ManuscriptContentResource',
                                full=True, null=True)
    pieces = EmbeddedListField(attribute='pieces',
                               of='hymnbooks.apps.api.resources.PieceResource',
                               full=True, null=True)

    class Meta:
        object_class = models.Manuscript
        allowed_methods = ('get', 'post', 'patch', 'delete')
        filtering = {
            'status': ALL,
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        excludes = ('id',)
        authentication = MultiAuthentication(AppApiKeyAuthentication(), 
                                             CookieBasicAuthentication())
        authorization = AnyoneCanViewAuthorization()

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'slug', 'title',
                                  self.Meta.object_class)
        return bundle
