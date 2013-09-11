from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('hymnbooks.apps.core.urls')),
    url(r'^cms/', include('hymnbooks.apps.cms.urls')),
)
