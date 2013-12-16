from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.views.generic import ListView
from django.utils.encoding import force_unicode
from django.conf import settings

from hymnbooks.apps.core import models
from hymnbooks.apps.cms import forms


class SectionView(View):
    doc_type = models.Section
    form_class = forms.SectionForm
    template_name = 'section.html'
    initial = {'name': '', 'description': '', 'status': 'draft'}

    def get(self, request, *args, **kwargs):
        context_object_name = '_'.join([self.doc_type.__name__,
                                        'objects']).lower()
        context_objects = self.doc_type.objects(status__ne='deleted')
        section_slug = kwargs.get('section_slug', None)
        try:
            document = self.doc_type.objects.get(slug=section_slug)
        except:
            document = None
        if kwargs.get('display_form', False):
            if document:
                form = self.form_class(instance=document)
            else:
                form = self.form_class(initial=self.initial)
        else:
            form = None
        return render(request, self.template_name,
                      {'form': form, 'document': document,
                       context_object_name: context_objects})

    def post(self, request, *args, **kwargs):
        form = forms.SectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('section_list'))
        else:            
            return render(request, self.template_name,
                          {'form': form})


class FileUploadView(View):
    template_name = 'cms/form_upload.html'
    form_class = forms.UploadFileForm

    def get(self, request, *args, **kwargs):
        context_objects = []
        status = {'status__ne': 'deleted'}
        context_objects_type = kwargs.get('show_only', '')
        if context_objects_type == 'images':
            context_objects.extend(list(models.ContentImage.objects(**status)))
        elif context_objects_type == 'audio':
            # bookmark: extract audio only from Manuscript -> Piece -> audio
            pass
        else:
            # extract everything
            context_objects.extend(list(models.ContentImage.objects(**status)))
        return render(request, self.template_name,
                      {'form': self.form_class(),
                       'context_objects': context_objects})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            self.handle_uploaded_file(request)
            return redirect(reverse('upload'))
        return render(request, self.template_name, {'form': form})

    def handle_uploaded_file(self, request):
        upload_file = request.FILES['file']
        name = request.POST.get('name', force_unicode(upload_file))
        image = models.ContentImage(name=name)
        image.image.put(upload_file, content_type = 'image/jpeg')

        # bookmark:
        # Warning!
        # The field `created_by` is being temporarily substituted by user "beta", if not logged on.
        # However, when the authentication works, the following should be added here:
        #
        # from django.contrib.auth.decorators import login_required
        # @login_required
        # def handle_uploaded_file(self, request):
        # ...

        if request.user.is_anonymous():
            request.user = models.MongoUser.objects.get(username=u"beta")

        image.save(request=request)
        return
