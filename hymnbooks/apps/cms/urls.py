from django.conf.urls.defaults import url
from django.conf.urls.defaults import patterns

from hymnbooks.apps.cms import views as cms_views

urlpatterns = patterns('',
    url(r'^frame$', cms_views.FrameView.as_view()),
)
