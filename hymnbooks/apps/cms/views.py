from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.views.generic import ListView
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
