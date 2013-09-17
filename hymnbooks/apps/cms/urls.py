from django.conf.urls import url
from django.conf.urls import patterns

from hymnbooks.apps.cms import views as cms_views

urlpatterns = patterns('',

    # List of available frames.
    url(r'^section/$', cms_views.SectionView.as_view(),
        name='section_list'),
    
    # Section details.
    url(r'^section/(?P<section_slug>[-\w]+)/$', cms_views.SectionView.as_view(),
        name='section_detail'),
        
    # Add new section.
    url(r'^section/add$', cms_views.SectionView.as_view(),
        {'display_form': True},
        name='section_add'),

    # Save new section.
    url(r'^section/save$', cms_views.SectionView.as_view(),
        {'display_form': True},
        name='section_save_new'),

    # Save current section.
    url(r'^section/(?P<section_id>\w+)/save$', cms_views.SectionView.as_view(),
        {'display_form': True},
        name='section_save'),
)
