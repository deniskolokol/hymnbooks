from django.conf.urls import patterns, url

from hymnbooks.apps.medialib import views

urlpatterns = patterns('',
    # Media library root
    url(r'^$', views.MediaLibraryView.as_view(),
        name='medialib_root'),

    # Upload files to the root folder.
    url(r'^upload/$', views.FileUploadView.as_view(),
        name='medialib_upload_to_root'),

    # Create new folder in root.
    url(r'^newfolder/$', views.NewFolderView.as_view(),
        name='medialib_newfolder_in_root'),

    # Media library: Content of a given folder.
    url(r'^(?P<container>[-\w]+)/$', views.MediaLibraryView.as_view(),
        name='medialib_container'),

    # Upload files to a current container.
    url(r'^(?P<container>[-\w]+)/upload/$', views.FileUploadView.as_view(),
        name='medialib_upload_to_container'),

    # Create new folder inside a current container.
    url(r'^(?P<container>[-\w]+)/newfolder/$', views.NewFolderView.as_view(),
        name='medialib_newfolder_in_container'),

    # Media library: Content of a given folder.
    url(r'^(?P<id>[-\w]+)/delete/$', views.MediaLibraryDelete.as_view(),
        name='medialib_delete'),

)
