from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.template import RequestContext
from django.utils.encoding import force_unicode
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from hymnbooks.apps.core.models import MediaLibrary
from hymnbooks.apps.core.utils import UserMessage
from hymnbooks.apps.medialib import forms
from hymnbooks.settings import base

import mongoengine


# HELPER FUNCTIONS

def get_media_object(**kwargs):
    try:
        obj = MediaLibrary.objects.get(pk=kwargs['container'])
    except:
        obj = None
    return obj


def get_MediaLibrary(request, *args, **kwargs):
    """
    Returns a QuerySet in case if kwargs['container'] points to None or folder,
    otherwise - MediaLibrary object.
    """
    lib_filter = {}

    # Return active elements by default.
    status = kwargs.get('status', None)
    if status is None:
        lib_filter.update({'status__ne': 'deleted'})

    container = kwargs.get('container', None)
    if container:
        lib_filter.update({'container': container})
    else:
        lib_filter.update({'container': None})

    media_object = get_media_object(**lib_filter)
    if media_object:
        if media_object.is_file:
            return media_object

    return MediaLibrary.objects.filter(**lib_filter)\
      .order_by('is_file', 'name')


def reverse_back(**kwargs):
    if kwargs.get('container', None):
        return redirect(reverse('medialib_container',
                                args=(kwargs['container'],)))
    return redirect(reverse('medialib_root'))


class MediaLibraryView(View):
    template_name = 'medialib.html'

    def get(self, request, *args, **kwargs):
        context_objects = get_MediaLibrary(request, *args, **kwargs)
        if isinstance(context_objects, MediaLibrary):

            # Display file.
            return HttpResponse(context_objects.mediafile.read(),
                                content_type=context_objects.mediafile.content_type)

        # Display folder content.
        return render(request,
                      self.template_name,
                      {'form': None,
                       'context_objects': context_objects,
                       'user_message': request.session.pop('user_message', {})
                       },
                       context_instance=RequestContext(request))


class FileUploadView(View):
    template_name = 'medialib.html'
    form_class = forms.UploadFileForm

    def get(self, request, *args, **kwargs):
        context_objects = get_MediaLibrary(request, *args, **kwargs)
        return render(request,
                      self.template_name,
                      {'form': self.form_class(),
                       'context_objects': context_objects,
                       'user_message': request.session.pop('user_message', {})
                       },
                       context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            container = get_media_object(**kwargs)
            request.session['user_message'] = self.handle_upload(
                form.cleaned_data['file'], container, request)
            return reverse_back(**kwargs)

        return render(request,
                      self.template_name,
                      {'form': form},
                      context_instance=RequestContext(request))

    def handle_upload(self, in_memory, container, request):
        # Warning!
        # The field `created_by` temporarily substituted by superuser, if not logged on.
        # However, when the authentication works, use @login_required
        # from django.contrib.auth.decorators
        if request.user.is_anonymous():
            from hymnbooks.apps.core.models import MongoUser
            request.user = MongoUser.objects.get(username=u"beta")

        mediafile = MediaLibrary(name=force_unicode(in_memory.name),
                                 container=container)
        mediafile.mediafile.put(in_memory, content_type=in_memory.content_type)
        try:
            mediafile.save(request=request)
        except mongoengine.errors.NotUniqueError:
            message = _('File with this name already exists!')
            return UserMessage(message).danger()

        return # no news, good news


class NewFolderView(View):
    template_name = 'medialib.html'
    form_class = forms.FolderForm

    def get(self, request, *args, **kwargs):
        context_objects = get_MediaLibrary(request, *args, **kwargs)
        return render(request,
                      self.template_name,
                      {'form': self.form_class(),
                       'context_objects': context_objects,
                       'user_message': request.session.pop('user_message', {})
                       },
                      context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            container = get_media_object(**kwargs)
            request.session['user_message'] = self.create_folder(
                form.cleaned_data['name'], container, request)
            return reverse_back(**kwargs)

        return render(request,
                      self.template_name,
                      {'form': form},
                      context_instance=RequestContext(request))

    def create_folder(self, name, container, request):
        # Warning!
        # The field `created_by` temporarily substituted by superuser, if not logged on.
        # However, when the authentication works, use @login_required
        # from django.contrib.auth.decorators
        if request.user.is_anonymous():
            from hymnbooks.apps.core.models import MongoUser
            request.user = MongoUser.objects.get(username=u"beta")

        folder = MediaLibrary(name=name, container=container, is_file=False)
        try:
            folder.save(request=request)
        except mongoengine.errors.NotUniqueError:
            message = _('Folder with this name already exists!')
            return UserMessage(message).danger()

        return # no news, good news


class MediaLibraryDelete(View):
    template_name = 'medialib.html'

    def get(self, request, **kwargs):
        media_item = MediaLibrary.objects.get(id=kwargs['id'])

        rev_kwargs = {}
        if media_item.container:
            rev_kwargs = {'container': media_item.container.id}
        try:
            media_item.delete()
        except Exception as e:
            request.session['user_message'] = UserMessage(message).danger(str(e))
            
        return reverse_back(**rev_kwargs)
