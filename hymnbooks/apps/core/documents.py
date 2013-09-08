from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from datetime import datetime


FIELD_TYPE = (('string', _('String field')),
              ('number', _('Number field')),
              ('list', _('List of values')),
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
    Describes a field.
    """
    field_name = StringField50(required=True)
    field_type = StringField10(choices=FIELD_TYPE, default='string')
    field_required = BooleanField(required=True, default=False)
    field_description = StringField200()
    field_internal_class = StringField()
    frame = ReferenceField(Frame)

    def __unicode__(self):
        return self.field_name


class Metadata(EmbeddedDocument):
    """
    Describes the structure of the fields in an arbitrary collection.
    """
    collection_name = StringField200(required=True)
    fields = ListField(EmbeddedDocumentField(DataField))

    def __unicode__(self):
        return self.collection_name


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
    metadata = EmbeddedDocumentField(Metadata)

    def __unicode__(self):
        return self.text if len(self.text) <= 75 else self.text[:75].strip() + '...'
    

class Role(EmbeddedDocument):
    """
    Roles, such as authors, copyrighters, etc.
    """
    role = StringField(required=True)
    metadata = EmbeddedDocumentField(Metadata)

    def __unicode__(self):
        return self.role


class ResponsibilityStatement(EmbeddedDocument):
    """
    Responsibilities: names of Authors, Copyrighters, etc.
    """
    role = ListField(EmbeddedDocumentField(Role))
    name = StringField(required=True)

    def __unicode__(self):
        return '%s: %s' % (self.role, self.name)


class BibliographicCitation(EmbeddedDocumentField):
    """
    Bibliographic Citation in the ManuscriptContent.
    """
    author = StringField200(required=True)
    title = StringField200(required=True)
    place_of_publishing = StringField200(required=True) # how to automate cities? multilingual!
    date_of_publishing = StringField()
    scope_of_citation = StringField50()


class ContentImage(EmbeddedDocument):
    """
    Images of manuscript content.
    """
    page_number = IntField()
    image_id = StringField10(required=True)
    image = ImageField(thumbnail_size=(150, 100, True))
    preview = ImageField(size=(300, 200, True))
    

class ManuscriptContent(EmbeddedDocument):
    """
    The description of the Content of a Manuscript.
    """
    raw_title = StringField(required=True)
    title = ListField(StringField(required=True))
    image = ListField(EmbeddedDocumentField(ContentImage))
    metadata = EmbeddedDocumentField(Metadata)

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

    # Technical info.
    updated = DateTimeField(default=datetime.now)

    metadata = EmbeddedDocumentField(Metadata)

    def __unicode__(self):
        return self.title


# Warning! Following data to be uploaded initially,
# there shouldn't be field descriptions in the documents structure
#
class InitialProposedFields(Document):
    collection_name = ListField()
    fields = ListField()

    def __init__(self, *args, **kwargs):
        super(InitialProposedFields, self).__init__(*args, **kwargs)
        collection_fields = {
            'ManuscriptContent': [
                {
                    'field_name': 'locus',
                    'field_description': _('Locus'),
                    'field_type': 'string',
                    'field_required': False
                    },
                {
                    'field_name': 'responsibility',
                    'field_description': _('Responsibility'),
                    'field_type': 'list',
                    'field_required': False,
                    'field_internal_class': 'ResponsibilityStatement'
                    },
                {
                    'field_name': 'imprint',
                    'field_description': _('Imprint'),
                    'field_type': 'list',
                    'field_required': False,
                    },
                {
                    'field_name': 'explicit',
                    'field_description': _('Explicit'),
                    'field_type': 'string',
                    'field_required': False
                    },
                {
                    'field_name': 'rubric',
                    'field_description': _('Rubric'),
                    'field_type': 'string',
                    'field_required': False
                    },
                {
                    'field_name': 'text_language',
                    'field_description': _('Text language'),
                    'field_type': 'string',
                    'field_required': False
                    },
                {
                    'field_name': 'bibliographic_citation',
                    'field_description': _('Bibliographic citation'),
                    'field_type': 'list',
                    'field_required': False,
                    'field_internal_class': 'BibliographicCitation'
                    }
                ],
            'Manuscript': [
                {
                    'field_name': 'id_specific',
                    'field_description': _('Specific ID'),
                    'field_type': 'string',
                    'field_required': True,
                    'frame_name': _('Identification')
                    },
                {
                    'field_name': 'id_type',
                    'field_description': _('Type ID'),
                    'field_type': 'string',
                    'field_required': False,
                    'frame_name': _('Identification')
                    },
                {
                    'field_name': 'id_no',
                    'field_description': _('No ID'),
                    'field_type': 'string',
                    'field_required': True,
                    'frame_name': _('Identification')
                    },
                {
                    'field_name': 'repository',
                    'field_description': _('Repository'),
                    'field_type': 'string',
                    'field_required': True,
                    'frame_name': _('Identification')
                    },
                {
                    'field_name': 'record_responsible_name',
                    'field_description': _('Responsible for the record'),
                    'field_type': 'string',
                    'field_required': False,
                    'frame_name': _('Record')
                    },
                {
                    'field_name': 'record_responsible_institution',
                    'field_description': _('Institution responsible for the record'),
                    'field_type': 'list',
                    'field_required': False,
                    'frame_name': _('Record')
                    },
                {
                    'field_name': 'object_description',
                    'field_description': _('Object description'),
                    'field_type': 'list',
                    'field_required': False,
                    'frame_name': _('Physical description')
                    },
                {
                    'field_name': 'extent',
                    'field_description': _('Extent'),
                    'field_type': 'string',
                    'field_required': False,
                    'frame_name': _('Physical description')
                    },
                {
                    'field_name': 'dimensions',
                    'field_description': _('Dimensions'),
                    'field_type': 'string',
                    'field_required': False,
                    'frame_name': _('Physical description')
                    },
                {
                    'field_name': 'place_of_origin',
                    'field_description': _('Place of origin'),
                    'field_type': 'string',
                    'field_required': False,
                    'frame_name': _('History')
                    },
                {
                    'field_name': 'date_of_origin',
                    'field_description': _('Date of origin'),
                    'field_type': 'string',
                    'field_required': False,
                    'frame_name': _('History')
                    },
                {
                    'field_name': 'facsimile',
                    'field_description': _('Facsimile'),
                    'field_type': 'string',
                    'field_required': False
                    },
                ]
            }
        
        collection_name = kwargs.get('collection_name', None)

        if collection_name:
            self.fields = collection_fields[collection_name]
