from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from .utils import slugify_unique

from datetime import datetime

"""
Dynamic fields type.
"""
FIELD_TYPE = (('string', _('String field')),
              ('number', _('Number field')),
              ('document', _('Document field')),
              ('list', _('List of values or documents')),
              ('image', _('Image field')))

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
        self.slug = slugify_unique(self.title, self.__class__)

        super(GenericSlugDocument, self).save(*args, **kwargs)


class FieldDefinition(EmbeddedDocument):
    """
    Describes a field in the structure of an arbitrary collection.
    """
    field_name = StringField(required=True)
    field_label = StringField()
    field_type = StringField(choices=FIELD_TYPE, default='string')
    field_required = BooleanField(required=True, default=False)
    field_description = StringField()
    field_internal_class = StringField()
    field_display = BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Overrides save method: updates.
        """
        # Fill out `field_label` field if not given.
        self.field_label = '' if self.field_label is None else self.field_label.strip()
        if self.field_label == '':
            self.field_label = self.field_name.replace('_', ' ').title()

            # Warning!
            # Here must be regexp getting rid of all non-alphanumeric characters!
            # And also downcode it!
            # But do it first on a client side with JS! User must see its creation, 
            # but not necessarily intrude into it.

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
    image = ImageField(thumbnail_size=(150, 100, True))
    preview = ImageField(size=(300, 200, True))


class Voice(EmbeddedDocument):
    """
    Separate voice / instrument in the scores (either voice or instrument).
    """
    voice_type = StringField200()
    voice_name = StringField200()
    description = StringField()
    image_ref = ReferenceField(ContentImage)
    image_crop = ListField() # pixels coords of top-left and bottom-right corners
                             # 4 numbers tuple: (X_tl, Y_tl, X_br, Y_br)
    auxdata = DictField()
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
    scores = FileField(help_text=_(u'Scores'))

    auxdata = DictField()
    metadata = ListField(ReferenceField(Section))


class ManuscriptContent(GenericDocument, EmbeddedDocument):
    """
    Actual Manuscript content (scan parts and description).
    """
    page_index = StringField50(required=True, help_text=_(u'Page index'))
    page_description = StringField(required=True, help_text=_(u'Description'))
    image_ref = ReferenceField(ContentImage)

    auxdata = DictField()
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

    auxdata = DictField()
    metadata = ListField(EmbeddedDocumentField(FieldDefinition))
