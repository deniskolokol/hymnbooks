from django import forms
from django.utils.translation import ugettext_lazy as _
from mongoforms import MongoForm

from hymnbooks.apps.core import models


class UploadFileForm(forms.Form):
    # file = forms.FileField(class="form-control" placeholder="Search")
    file = forms.FileField(label=_(u'Choose a file to upload'), 
                           widget=forms.ClearableFileInput(
                               attrs={
                                   'class': 'form-control',
                                   'placeholder': _(u'Choose a file to upload')
                                   }))

class FolderForm(MongoForm):
    class Meta:
        document = models.MediaLibrary
        fields = ('name',)

    name = forms.CharField(label=_(u'Create new folder'), 
                           widget=forms.TextInput(
                               attrs={
                                   'class': 'form-control',
                                   'placeholder': _(u'Folder name')
                                   }))
