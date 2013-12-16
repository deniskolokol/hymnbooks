from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.template import RequestContext
from django.utils.encoding import force_unicode


from hymnbooks.apps.core import models
from hymnbooks.apps.medialib import forms


# HELPER FUNCTIONS

def get_MediaLibrary(request, *args, **kwargs):
    """
    Filter items from medialibrary depending on status,
    container folder, etc.
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

    return models.MediaLibrary.objects.filter(**lib_filter)


def get_container(**kwargs):
    try:
        container = models.MediaLibrary.objects.get(pk=kwargs['container'])
    except:
        container = None
    return container


def reverse_back(**kwargs):
    if kwargs.get('container', None):
        return redirect(reverse('medialib_container',
                                args=(kwargs['container'],)))
    return redirect(reverse('medialib_root'))


class MediaLibraryView(View):
    template_name = 'medialib.html'

    def get(self, request, *args, **kwargs):
        context_objects = get_MediaLibrary(request, *args, **kwargs)
        return render(request, self.template_name,
                      {'form': None, 'context_objects': context_objects},
                      context_instance=RequestContext(request))


class FileUploadView(View):
    template_name = 'medialib.html'
    form_class = forms.UploadFileForm

    def get(self, request, *args, **kwargs):
        context_objects = get_MediaLibrary(request, *args, **kwargs)
        return render(request, self.template_name,
                      {'form': self.form_class(), 'context_objects': context_objects},
                      context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            container = get_container(**kwargs)
            self.handle_upload(form.cleaned_data['file'], container, request)
            return reverse_back(**kwargs)
        return render(request, self.template_name, {'form': form},
                      context_instance=RequestContext(request))

    def handle_upload(self, in_memory, container, request):
        # Warning!
        # The field `created_by` temporarily substituted by superuser, if not logged on.
        # However, when the authentication works, use @login_required
        # from django.contrib.auth.decorators
        if request.user.is_anonymous():
            request.user = models.MongoUser.objects.get(username=u"beta")

        mediafile = models.MediaLibrary(name=force_unicode(in_memory.name),
                                        container=container)
        mediafile.mediafile.put(in_memory, content_type=in_memory.content_type)
        mediafile.save(request=request)
        return

class NewFolderView(View):
    template_name = 'medialib.html'
    form_class = forms.FolderForm

    def get(self, request, *args, **kwargs):
        context_objects = get_MediaLibrary(request, *args, **kwargs)
        return render(request, self.template_name,
                      {'form': self.form_class(), 'context_objects': context_objects},
                      context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            container = get_container(**kwargs)
            self.create_folder(form.cleaned_data['name'], container, request)
            return reverse_back(**kwargs)
        return render(request, self.template_name, {'form': form},
                      context_instance=RequestContext(request))

    def create_folder(self, name, container, request):
        # Warning!
        # The field `created_by` temporarily substituted by superuser, if not logged on.
        # However, when the authentication works, use @login_required
        # from django.contrib.auth.decorators
        if request.user.is_anonymous():
            request.user = models.MongoUser.objects.get(username=u"beta")

        folder = models.MediaLibrary(name=name, container=container,
                                     is_file=False)
        folder.save(request=request)
        return