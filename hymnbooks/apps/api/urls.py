from django.conf.urls import *
from tastypie.api import Api

from hymnbooks.apps.api import resources

v1_api = Api(api_name='v1')

v1_api.register(resources.FieldTypeResource())
v1_api.register(resources.SectionResource())
v1_api.register(resources.ManuscriptResource())

urlpatterns = patterns('',
   (r'^', include(v1_api.urls)),
)
