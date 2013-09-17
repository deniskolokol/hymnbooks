from django import forms
from mongoforms import MongoForm
from hymnbooks.apps.core import models

class SectionForm(MongoForm):
    class Meta:
        document = models.Section
        fields = ('title', 'description')

    title = forms.CharField()
    description = forms.CharField(widget=forms.Textarea, required=False)
