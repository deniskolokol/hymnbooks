from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from datetime import datetime


FIELD_TYPE = (('string', _('String field')),
              ('number', _('Number field')),
              ('document', _('Document field')),
              ('list', _('List of values or documents')),
              ('image', _('Image field')))


class StringFieldInternal(StringField):
    def __init__(self, *args, **kwargs):
        super(StringFieldInternal, self).__init__(*args, **kwargs)
    
    def get_internal_type(self):
        return 'StringField'

class StringField10(StringFieldInternal):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 10)
        super(StringField10, self).__init__(*args, **kwargs)

class StringField50(StringFieldInternal):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 50)
        super(StringField50, self).__init__(*args, **kwargs)
    
class StringField200(StringFieldInternal):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 200)
        super(StringField200, self).__init__(*args, **kwargs)


class Frame(Document):
    """
    Defines a collection of fields, grouped by a similar subject.
    """
    frame_title = StringField50(required=True)

    def __unicode__(self):
        return self.frame_title


class DataField(EmbeddedDocument):
    """
    Describes a field in the structure of an arbitrary collection.
    """
    field_name = StringField50(required=True)
    field_label = StringField50()
    field_type = StringField10(choices=FIELD_TYPE, default='string')
    field_required = BooleanField(required=True, default=False)
    field_description = StringField200()
    field_internal_class = StringField()
    field_display = BooleanField(default=False)
    frame = ReferenceField(Frame)

    def save(self, *args, **kwargs):
        """
        Overrides save method: updates.
        """
        # Fill out `field_label` field if not given.
        self.field_label = '' if self.field_label is None else self.field_label.strip()
        if self.field_label == '':
            self.field_label = self.field_name.replace('_', ' ').title()
        super(DataField, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.field_label
    

class Publisher(Document):
    code = StringField10(required=True)
    title = StringField200(required=True)
    metadata = EmbeddedDocumentField(Metadata)

    def __unicode__(self):
        return ('%s %s' % (self.code, self.title)).strip()


class UserNote(EmbeddedDocument):
    datetime = DateTimeField(default=datetime.now)
    user = StringField(required=True) # NB: mongoengine users!
    text = StringField(required=True)

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(DataField))    

    def __unicode__(self):
        return self.text if len(self.text) <= 75 else self.text[:75].strip() + '...'


class ResponsibilityStatement(EmbeddedDocument):
    """
    Responsibilities: names of Authors, Copyrighters, etc.
    """
    name = StringField200(required=True)
    role = StringField200(required=True)

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(DataField))    

    def __unicode__(self):
        return '%s: %s' % (self.role, self.name)


class ContentImage(EmbeddedDocument):
    """
    Images of manuscript content.
    """
    page_number = IntField()
    image_id = StringField10(required=True)
    image = ImageField(thumbnail_size=(150, 100, True))
    preview = ImageField(size=(300, 200, True))

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(DataField))

class Voice():
    """
    Separate voice / instrument in the scores (either voice or instrument).
    """

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(DataField))
    

class ManuscriptContent(EmbeddedDocument):
    """
    The description of the Content of a Manuscript.
    """
    raw_title = StringField(required=True)
    title = ListField(StringField(required=True))
    image = ListField(EmbeddedDocumentField(ContentImage))

    voices = ListField(EmbeddedDocumentField(Voice))

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(DataField))    

    def save(self, *args, **kwargs):
        """
        Overrides save method: updates.
        """
        # Fill out `title` field as parts of raw_title.
        self.raw_title = self.raw_title.strip()
        if '/' in self.raw_title:
            self.title = self.raw_title.split('/').strip()
        else:
            self.title = [self.raw_title]
        super(ManuscriptContent, self).save(*args, **kwargs)

    def __unicode__(self):
        return " / ".join(self.title)


class Manuscript(Document):
    """
    Main container for manuscripts.
    """
    # Title and Publication Statement.
    title = StringField(required=True)
    author = ListField(StringField200(), required=True)

    # Basic information.
    country = StringField50(required=True) # django_countries? multilingual!
    settlement = StringField200(required=True) # how to automate cities? multilingual!

    # Publication Statement.
    publisher = ReferenceField(Publisher)

    # Contents.
    manuscripts_content = ListField(EmbeddedDocumentField(ManuscriptContent))

    # Scanned document.
    image = ListField(EmbeddedDocumentField(ContentImage), required=True)

    # Technical info.
    updated = DateTimeField(default=datetime.now)

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(DataField))    

    def __unicode__(self):
        return self.title
