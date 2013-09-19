from tastypie import fields 
from tastypie.resources import Resource
from tastypie.authorization import Authorization
from tastypie_mongoengine.resources import MongoEngineResource
from tastypie_mongoengine.fields import EmbeddedDocumentField

from hymnbooks.apps.core import models


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
        list_allowed_methods = ['get']
        detail_allowed_methods = []
        authorization = Authorization()

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

    
class ManuscriptContentResource(MongoEngineResource):
    class Meta:
        object_class = models.ManuscriptContent

        
class ManuscriptResource(MongoEngineResource):
    """
    Manuscript data.
    """
    content = EmbeddedDocumentField(
        embedded='hymnbooks.apps.api.resources.ManuscriptContentResource',
        attribute='content')
    
    class Meta:
        queryset = models.Manuscript.objects.all()
        allowed_methods = ('get', 'post', 'put', 'delete')
        authorization = Authorization()
