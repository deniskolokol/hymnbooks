from django.conf.urls.defaults import url
from django.conf.urls.defaults import patterns

from hymnbooks.apps.core import views as core_views

urlpatterns = patterns('',
    url(r'^library$', core_views.LibraryView.as_view()),
)
