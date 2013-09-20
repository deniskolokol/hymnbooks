from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from hymnbooks.apps.core import utils

from datetime import datetime

"""
Dynamic fields type.
"""
FIELD_TYPE = (('string', _('String values')),
              ('number', _('Number values')),
              ('boolean', _('True of False')),
              ('document', _('Document class')))

"""
Document status.
- Every time a new document is created, it is becoming 'draft'
  (for the purpose of autosave "behind the scenes").
- Saving newly created document is changing its status to 'active'.
- Suspending a document is sending it to the review.
- Deleting a document: 
  -- changing its status followed by notification to the moderator,
     who created the document (if the User who deletes it is different
     from the one who created it)
  -- otherwise simple delete.
"""
DOCUMENT_STATUS = (('draft', _('Draft')),
                   ('active', _('Active')),
                   ('suspended', _('Suspended')),
                   ('deleted', _('Deleted')))


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

class GenericDocument(Document):
    """
    Abstract class for all vocabulary-like documents.
    """
    title = StringField(required=True, help_text=_(u'Title'))
    created = DateTimeField(help_text=_(u'Created'))
    last_updated = DateTimeField(help_text=_(u'Last updated'))
    created_by = StringField(help_text=_(u'Created by'))
    updated_by = StringField(help_text=_(u'Updated by'))
    status = StringField(choices=DOCUMENT_STATUS, default='draft')
    note = StringField()

    meta = {'abstract': True}

    def save(self, *args, **kwargs):
        """
        Takes care of proper dates, users, etc.
        """
        if not self.created:
            self.created = datetime.now()
        self.last_updated = datetime.now()

        super(GenericDocument, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title

class GenericSlugDocument(GenericDocument):
    """
    Abstract class for all vocabularies with slugs.
    """
    slug = StringField(unique=True, help_text=_(u'Slug'))

    meta = {'abstract': True}

    def save(self, *args, **kwargs):
        """
        Takes care of unique slug value.
        """
        self.slug = utils.slugify_unique(self.title, self.__class__)

        super(GenericSlugDocument, self).save(*args, **kwargs)


class FieldDefinition(EmbeddedDocument):
    """
    Describes a field in the structure of an arbitrary collection.

    * `field_type` allows for the references on the other Documents defined in
    core.models or as Section models in database.

    * Values of a field actually represented as lists. Even if only one value 
    is required (such as field_x = 1), it will be stored as a list with the 
    length of 1 (i.e. field_x = [1]). `field_max_count` specifies the maximum 
    number of elements in such lists.
    """
    field_label = StringField(required=True, help_text=_(u'Label'))
    field_name = StringField(required=True, help_text=_(u'Name'))
    field_type = StringField(choices=FIELD_TYPE, default='string',
                             help_text=_(u'Type'))
    field_internal_class = StringField(help_text=_(u'Document class'))
    field_required = BooleanField(required=True, default=False,
                                  help_text=_(u'Required'))
    field_description = StringField(help_text=_(u'Description (optional)'))
    field_display = BooleanField(default=False,
                                 help_text=_(u'Display this field by default'))
    field_max_count = FloatField(default=float("inf"),
                                 help_text=_(u'Maximum number of elements'))

    def save(self, *args, **kwargs):
        """
        Overrides save method: updates.
        """
        # Fill out `field_name` if not given.
        # Warning! This should be a back-end protection for the client-side JS.
        self.field_name = '' if self.field_name is None else self.field_name.strip()
        if self.field_name == '':
            self.field_name = utils.slugify_downcode(self.field_label)

        super(FieldDefinition, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.field_label


class Section(GenericSlugDocument):
    """
    Defines a section in the document that consists of fields,
    grouped by a similar subject.
    """
    description = StringField(help_text=_(u'Description'))
    fields = ListField(EmbeddedDocumentField(FieldDefinition),
                       help_text=_(u'Fields'))

    meta = {'collection': 'cmsSection'}


class ContentImage(GenericDocument):
    """
    Images of manuscript content.

    Not for embedding, but for referensing from other documents
    (in particular from Manusacript, Content, and eventually Piece).
    """
    image_id = StringField10(required=True)

    # # WARNING! Revert back to ImageField after installing PIL!
    # image = ImageField(thumbnail_size=(150, 100, True))
    # preview = ImageField(size=(300, 200, True))
    image = FileField()
    preview = FileField()



class Voice(EmbeddedDocument):
    """
    Separate voice / instrument in the scores (either voice or instrument).
    """
    voice_type = StringField200()
    voice_name = StringField200()
    description = StringField()
    image_ref = ReferenceField(ContentImage)

    data = DictField()
    metadata = ListField(ReferenceField(Section))
    

class Piece(GenericDocument, EmbeddedDocument):
    """
    Musical piece.
    """
    author = ListField(StringField(), required=True, help_text=_(u'Author(s)'))
    voices = ListField(EmbeddedDocumentField(Voice), help_text=_(u'Voices'))
    incipit = StringField(help_text=_(u'Incipit'))
    orig_mxml = StringField(help_text=_(u'Original MusicXML'))
    orig_mxml_data = DictField() # converted from XML for indexing and searching by notes
    audio = FileField(help_text=_(u'Audio example'))

    data = DictField()
    metadata = ListField(ReferenceField(Section))


class ManuscriptContent(GenericDocument, EmbeddedDocument):
    """
    Actual Manuscript content (scan parts and description).
    """
    page_index = StringField50(required=True, help_text=_(u'Page index'))
    page_description = StringField(help_text=_(u'Description'))
    image_ref = ReferenceField(ContentImage)

    data = DictField()
    metadata = ListField(ReferenceField(Section))


class Manuscript(GenericSlugDocument):
    """
    Main container for manuscripts.
    """
    description = StringField(help_text=_(u'Description'))
    content = ListField(EmbeddedDocumentField(ManuscriptContent),
                        help_text=_(u'Content'))
    pieces = ListField(EmbeddedDocumentField(Piece), help_text=_(u'Pieces'))
    image = ListField(ReferenceField(ContentImage))

    data = DictField()
    metadata = ListField(ReferenceField(Section))
