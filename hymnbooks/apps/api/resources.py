from django.utils.translation import ugettext as _

from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import Authentication, MultiAuthentication
from tastypie.authorization import Authorization, ReadOnlyAuthorization
from tastypie_mongoengine.resources import MongoEngineResource
from tastypie_mongoengine.fields import *

from hymnbooks.settings.base import API_NAME
from hymnbooks.apps.core import models, utils
from hymnbooks.apps.api.auth import AppApiKeyAuthentication, \
     CookieBasicAuthentication, AnyoneCanViewAuthorization, \
     StaffAuthorization, AppAuthorization


DATE_FILTERS = ('exact', 'lt', 'lte', 'gte', 'gt', 'ne')


# HELPER FUNCTIONS

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
    try:
        value = data[field].strip() if data[field].strip() != '' else None
    except:
        value = None

    if value: # It is all right.
        return data
    
    try:
        data[field] = utils.slugify_unique(data[field_fro],
                                           obj_class,
                                           slugfield=field)
    except AttributeError: # `obj_class` not specified.
        data[field] = utils.slugify_downcode(data[field_fro])

    except: # Nothing have worked.
        data[field] = ''

    # Empty string is not an error, but cannot be accepted as a slug!
    if data[field].strip() == '':
        data[field] = utils.id_generator(size=20)

    return data


def process_instructions(data):
    """
    Processes fields with special instructions (__append, __delete, __move)
    """
    # Take care of `__append` keys
    append_keys = [k.rsplit('__', 1)[0] for k in data.keys() if '__append' in k]

    for key in append_keys:
        append_key = key + '__append'
        try:
            data[key].extend(utils.ensure_list(data.pop(append_key)))
        except KeyError:
            data[key] = [data.pop(append_key)]
        except Exception as e:
            print type(e), e
            data[key] = [data.pop(append_key)]

    # Take care of `__delete` keys
    delete_keys = [k.rsplit('__', 1)[0] for k in data.keys() if '__delete' in k]
    for key in delete_keys:
        delete_key = key + '__delete'
        index = data.pop(delete_key)
        try:
            data[key].pop(int(index))
        except (ValueError, TypeError, IndexError):
            pass # No such element or index given wrong, simply leave data as is.
        except Exception as e:
            pass # Do stuff only when it is right.

    return data


# RESOURCES

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
        authorization = StaffAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

class GroupResource(MongoEngineResource):
    permissions = EmbeddedListField(attribute='permissions',
                                    of='hymnbooks.apps.api.resources.DocumentPermissionResource',
                                    full=True, null=True)
    class Meta:
        object_class = models.MongoGroup
        resource_name = 'admin_group'
        excludes = ('id',)
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete',)
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())
        authorization = StaffAuthorization()

    def obj_get(self, bundle, **kwargs):
        bundle = super(GroupResource, self).obj_get(bundle, **kwargs)
        return bundle


class UserResource(MongoEngineResource):
    group = ReferencedListField(attribute='group',
                                of='hymnbooks.apps.api.resources.GroupResource',
                                full=True, null=True)
    permissions = EmbeddedListField(attribute='permissions',
                                    of='hymnbooks.apps.api.resources.DocumentPermissionResource',
                                    full=True, null=True)
    class Meta:
        resource_name = 'admin_user'
        object_class = models.MongoUser
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        excludes = ('id', 'password', 'api_key', 'api_key_created')
        filtering = {
            'username': ALL, # Filters are tuned to handle Authentication in the URL.
            'is_active': ('exact', 'ne'),
            'date_joined': DATE_FILTERS
            }
        authorization = StaffAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

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

    
class EndUserDataResource(MongoEngineResource):
    created_by = ReferenceField(attribute='created_by',
                                to='hymnbooks.apps.api.resources.UserResource',
                                full=True, null=True)
    updated_by = ReferenceField(attribute='updated_by',
                                to='hymnbooks.apps.api.resources.UserResource',
                                full=True, null=True)

    def reference_to_resource(self, field, data=None, resource_uri=''):
        key = field + '_resource_uri'
        if data is None:
            return {field: None, key: None}

        return {field: data.obj, key: '%s%s/' % \
                (resource_uri, str(data.obj.id))}
        
    def dehydrate(self, bundle, *args):
        """
        Use readable form of 'created_by' and 'updated_by' objects for display,
        add `resource_uri` for referensing to the actual objects.
        """
        if bundle.request.method == 'GET':
            fields = list(set(['created_by', 'updated_by'] + list(args)))

            for field in fields:
                obj_related = getattr(self, field)
                related = obj_related.get_related_resource(self)                

                bundle.data.update(
                    self.reference_to_resource(field,
                                               bundle.data[field],
                                               related.get_resource_uri()))
        return bundle

    def hydrate(self, bundle):
        """
        Fills on POST:
        - mandatory fields 'updated_by' and 'created_by'
        - processes <fieldname>__append and <fieldname>__delete keys 
          (returning correctly fulfilled <fieldname> instead)
        """
        try:
            bundle.data = process_instructions(bundle.data)
        except:
            # There might be resources that do not allow `sections` in their 
            # data (for example, SectionResource). Whatever wrong happens here,
            # simply go on, the data will remain intact.
            pass

        bundle.data['updated_by'] = bundle.request.user

        if bundle.obj:
            if bundle.obj.created_by is None:
                bundle.data['created_by'] = bundle.request.user

        return bundle


class FieldDefinitionResource(MongoEngineResource):
    embedded_section = ReferenceField(attribute='embedded_section',
                                      to='hymnbooks.apps.api.resources.SectionResource',
                                      full=True, null=True)
    class Meta:
        object_class = models.FieldDefinition
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        always_return_data = True

    def hydrate(self, bundle):
        bundle.data = ensure_slug(bundle.data, 'field_name', 'help_text')
        if 'embedded_section' in bundle.data:
            # It can be there, but can be null or empty.
            if not ((bundle.data['embedded_section'] is None) or
                    (len(bundle.data['embedded_section']) == 0)):
                bundle.data['field_type'] = 'embeddeddocument'
        return bundle


class SectionResource(EndUserDataResource):
    fields = EmbeddedListField(attribute='fields',
                               of='hymnbooks.apps.api.resources.FieldDefinitionResource',
                               full=True, null=True)
    class Meta:
        object_class = models.Section
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        excludes = ('id',)
        filtering = {
            'created_by': ALL,
            'updated_by': ALL,
            'status': ('exact', 'ne'),
            'created': DATE_FILTERS,
            'last_updated': DATE_FILTERS,
            }
        ordering = ('name', 'help_text', 'status', 'created', 'updated',)
        always_return_data = True
        authorization = AppAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

    def hydrate(self, bundle):
        bundle = super(SectionResource, self).hydrate(bundle)

        bundle.data = ensure_slug(bundle.data, 'name', 'help_text',
                                  self.Meta.object_class)
        return bundle


class SectionDataResource(MongoEngineResource):
    section = ReferenceField(attribute='section',
                             to='hymnbooks.apps.api.resources.SectionResource',
                             null=True, full=True)
    class Meta:
        object_class = models.SectionData
        resource_name = 'section_data'
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        always_return_data = True


class MediaLibraryResource(EndUserDataResource):
    sections = EmbeddedListField(attribute='sections',
                                 of='hymnbooks.apps.api.resources.SectionDataResource',
                                 full=True, null=True)
    container = ReferenceField(attribute='container',
                               to='hymnbooks.apps.api.resources.MediaLibraryResource',
                               null=True, full=True)

    class Meta:
        object_class = models.MediaLibrary
        resource_name = 'media_library'
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        excludes = ('id', 'mediafile', 'thumbnail', 'container_safe')
        filtering = {
            'created_by': ALL,
            'updated_by': ALL,
            'status': ('exact', 'ne'),
            'created': DATE_FILTERS,
            'updated': DATE_FILTERS,
            'container': ALL,
            'is_file': ALL
            }
        ordering = ('is_file', 'name', 'container', 'status', 'created', 'updated',)
        always_return_data = True
        authorization = AnyoneCanViewAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

    def dehydrate(self, bundle):
        args = ('container',)
        bundle = super(MediaLibraryResource, self).dehydrate(bundle, *args)

        if bundle.data['is_file']:
            bundle.data.update({
                'size': bundle.obj.mediafile.length,
                'size_pretty': utils.sizify(bundle.obj.mediafile.length),
                'content_type': bundle.obj.mediafile.content_type})

        return bundle


class EmbeddedMediaReferenceResource(MongoEngineResource):
    """
    Manage Media references: convert to and fro `id` and `resource_uri`.
    For subclassing only.
    """
    sections = EmbeddedListField(attribute='sections',
                                 of='hymnbooks.apps.api.resources.SectionDataResource',
                                 full=True, null=True)

    def dehydrate(self, bundle):
        """
        Fill media for display: convert id to resource_uri.
        """
        try:
            media = bundle.data['media']
        except KeyError:
            return bundle

        media_resource_uri = MediaLibraryResource().get_resource_uri()
        bundle.data['media'] = [
            {'resource_uri': '%s%s/' % (media_resource_uri, m.id)}
            for m in media]

        return bundle

    def hydrate(self, bundle):
        """
        Fill media for post or patch: get if from resource_uri.
        """
        bundle.data = process_instructions(bundle.data)

        try:
            media = bundle.data['media']
        except:
            return bundle

        bundle.data['media'] = [
            MediaLibraryResource().get_via_uri(m['resource_uri'],
                                               request=bundle.request).id
            for m in media]

        return bundle


class PieceResource(EmbeddedMediaReferenceResource):
    """
    Pieces data (list of documents, embedded into Manuscript).
    """
    class Meta:
        object_class = models.Piece
        always_return_data = True
        authorization = AnyoneCanViewAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())
        
class ManuscriptContentResource(EmbeddedMediaReferenceResource):
    """
    Manuscript content data (list of documents, embedded into Manuscript).
    """
    class Meta:
        object_class = models.ManuscriptContent
        always_return_data = True
        authorization = AnyoneCanViewAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

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
    sections = EmbeddedListField(attribute='sections',
                                 of='hymnbooks.apps.api.resources.SectionDataResource',
                                 full=True, null=True)
    media = ReferencedListField(attribute='media',
                                of='hymnbooks.apps.api.resources.MediaLibraryResource',
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
        ordering = ('name', 'title', 'status', 'created', 'updated',)
        always_return_data = True
        authorization = AnyoneCanViewAuthorization()
        authentication = MultiAuthentication(AppApiKeyAuthentication(),
                                             CookieBasicAuthentication())

    def hydrate(self, bundle):
        """
        If `name` is empty, fill it with unique slug obtained from title.
        If title is not given, use a random alphanumeric value.
        """
        bundle = super(ManuscriptResource, self).hydrate(bundle)

        bundle.data = ensure_slug(bundle.data,
                                  field='name',
                                  field_fro='title',
                                  obj_class=models.Manuscript)
        return bundle
