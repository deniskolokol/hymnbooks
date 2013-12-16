from django import forms
from mongoforms import MongoForm
from hymnbooks.apps.core import models

class SectionForm(MongoForm):
    class Meta:
        document = models.Section
        fields = ('name', 'description')

    name = forms.CharField()
    description = forms.CharField(widget=forms.Textarea, required=False)
