from hymnbooks.apps.api.resources import *

from django.conf.urls import *
from tastypie.api import Api

v1_api = Api(api_name=API_NAME)

v1_api.register(GroupResource())
v1_api.register(FieldTypeResource())
v1_api.register(SectionResource())
v1_api.register(ManuscriptResource())
v1_api.register(UserResource())
v1_api.register(PermissionResource())
v1_api.register(DocumentTypeResource())
v1_api.register(MediaLibraryResource())

urlpatterns = patterns('',
   (r'^', include(v1_api.urls)),
)
