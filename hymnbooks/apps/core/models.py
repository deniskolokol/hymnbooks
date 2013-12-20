from mongoengine import *
from mongoengine.django.auth import User

from django.utils.translation import ugettext_lazy as _

from datetime import datetime

from hymnbooks.apps.core import utils

import inspect


"""
Document status:
* Every time a new document is created, it is becoming 'draft'
  (for the purpose of autosave "behind the scenes").
* Saving newly created document is changing its status to 'active'.
* Suspending a document is sending it to the review.
* Deleting a document: 
  ** changing its status followed by notification to the moderator,
     who created the document (if the User who deletes it is different
     from the one who created it)
  ** otherwise simple delete.
"""
DOCUMENT_STATUS = (('draft', _('Draft')),
                   ('active', _('Active')),
                   ('suspended', _('Suspended')),
                   ('deleted', _('Deleted')))

# AUTHENTICATION AND AUTHORIZATION CLASSES
"""
Permission types that fit API requirements.
"""
PERMISSION_TYPE = (('create_detail', _('Create detail')),
                   ('create_list', _('Create list')),
                   ('read_list', _('Read list')),
                   ('read_detail', _('Read detail')),
                   ('update_list', _('Update list')),
                   ('update_detail', _('Update detail')),
                   ('delete_list', _('Delete list')),
                   ('delete_detail', _('Delete detail')))

"""
Document Types that should be defined on Permissions (analog of 
django's content_type). The class name of every Document, that is
not embedded, should be registered here.
"""
DOCUMENT_TYPE = (('MongoGroup', _('Group')),
                 ('MongoUser', _('User')),
                 ('MongoUserProfile', _('User profile')),
                 ('Section', _('Data section')),
                 ('LibraryItem', _('Library item')),
                 ('Manuscript', _('Manuscript')))


class GlobalPermission(EmbeddedDocument):
    """
    Permission that can be (but does not require being)
    attached to Document Type.
    """
    permission = StringField(required=True, choices=PERMISSION_TYPE,
                             help_text=_(u'Users can'))
    document_type = StringField(choices=DOCUMENT_TYPE,
                                help_text=_(u'Defined on'))

    def __unicode__(self):
        return u"can %s of %s" % (self.permission, self.document_type)


class PermissionControlDocument(Document):
    permissions = ListField(EmbeddedDocumentField(GlobalPermission),
                            help_text=_(u'Permissions'))
    meta = {'abstract': True}

    def ensure_no_duplicates_permissions(self):
        """
        Take care of duplicates in the permissions, on all fields. Doesn't
        depend on the structure of Permission.
        """
        permissions_clean = set([tuple(p.__dict__['_data'].items())
                                 for p in self.permissions])
        permissions_dicts = [dict((m[0], m[1]) for m in l)
                             for l in permissions_clean]
        self.permissions = [GlobalPermission(**kw) for kw in permissions_dicts]
    

class MongoGroup(PermissionControlDocument):
    """
    Groups of MongoUsers with assignment Permissions.
    """
    name = StringField(required=True, unique=True, help_text=_(u'Name'))

    meta = {'collection': 'admin_group'}

    def __unicode__(self):
        return self.name

    def has_permission(self, permission, document_type):
        try:
            MongoGroup.objects.get(id=self.id,
                                   permissions__permission=permission,
                                   permissions__document_type=document_type)
        except (MongoGroup.DoesNotExist, MongoGroup.MultipleObjectsReturned):
            return False

        return True

    def ensure_permission(self, permission, document_type):
        if not self.has_permission(permission, document_type):
            self.permissions.append(
                GlobalPermission(permission=permission,
                                 document_type=document_type))
            self.save()

    def save(self, *args, **kwargs):
        self.ensure_no_duplicates_permissions()
        
        super(MongoGroup, self).save(*args, **kwargs)
    

class MongoUser(User, PermissionControlDocument):
    """
    Subclass of mongoengine.django.auth.User with email as username
    and API key for authentication.
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']

    api_key = StringField(required=False, max_length=256, default='')
    api_key_created = DateTimeField(help_text=_(u'Created'))
    group = ListField(ReferenceField(MongoGroup))

    meta = {'collection': 'admin_user'}

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.set_api_key()

        self.ensure_no_duplicates_permissions()

        super(MongoUser, self).save(*args, **kwargs)

    def set_api_key(self):
        self.api_key = self.generate_key()
        self.api_key_created = datetime.now()

    def generate_key(self):
        import uuid, hmac
        from hashlib import sha1

        new_uuid = uuid.uuid4()
        return hmac.new(str(new_uuid), digestmod=sha1).hexdigest()

    def has_permission(self, permission, document_type):
        # No permissions for non-active users.
        if not self.is_active:
            return False

        # Check Group permissions.
        for group in self.group:
            if group.has_permission(permission, document_type):
                return True

        # Check individual permissions.
        try:
            MongoUser.objects.get(id=self.id,
                                  permissions__permission=permission,
                                  permissions__document_type=document_type)
        except (MongoUser.DoesNotExist, MongoUser.MultipleObjectsReturned):
            return False

        return True

    def __unicode__(self):
        return u"%s (%s)" % (self.username, self.get_full_name())


class MongoUserProfile(Document):
    """
    For future use: Profiler for MongoUser class.
    """
    dummy = StringField()

    meta = {'collection': 'user_profile'}


# DOCUMENT TEMPLATES
"""
Dynamic fields type:
* `number` field types generalized to float.
* `embeddeddocument` can only be documents of the type `Section`.
"""
FIELD_TYPE = (('string', _('String values')),
              ('float', _('Number values')),
              ('boolean', _('True of False')),
              ('embeddeddocument', _('Document type')))

class TemplateGenericDocument(Document):
    """
    Abstract class for all vocabulary-like documents.
    """
    name = StringField(required=True, help_text=_(u'Name'))
    created = DateTimeField(help_text=_(u'Created'))
    updated = DateTimeField(default=datetime.now, help_text=_(u'Last updated'))
    created_by = ReferenceField(MongoUser, help_text=_(u'Created by'))
    updated_by = ReferenceField(MongoUser, help_text=_(u'Updated by'))
    status = StringField(choices=DOCUMENT_STATUS, default='draft',
                         help_text=_(u'Status'))

    meta = {'abstract': True}

    def save(self, force_insert=False, validate=True, 
             clean=True, write_concern=None, cascade=None, 
             cascade_kwargs=None, _refs=None, **kwargs):
        """
        Auto-fill dates and users.
        """
        self.updated = datetime.now()
        if not self.created:
            self.created = self.updated

        if kwargs.get("request", None):
            self.updated_by = kwargs["request"].user
            if not self.created_by:
                self.created_by = self.updated_by

        super(TemplateGenericDocument, self).save(force_insert, validate,
            clean, write_concern, cascade, cascade_kwargs, _refs, **kwargs)

    def __unicode__(self):
        return self.name


class GenericDocument(TemplateGenericDocument):
    """
    Abstract class for all vocabulary-like documents with additional data
    stored in `data` field as a free-form dictionary.

    The structure of the dictionary: 1st level keys are names of Sections,
    followed by the list of values of the fields.
    """
    tags = ListField(StringField(), help_text=_(u'Tags'))
    sections = ListField(EmbeddedDocumentField('SectionData'),
                         help_text=_(u'Sections'))

    meta = {'abstract': True}


# MODERATOR'S DOCUMENTS

class FieldDefinition(EmbeddedDocument):
    """
    Describes a field in the structure of an arbitrary collection.

    * All values are actually lists. If there is only one element,
      the value of the field is [<value>]

    * `embedded_section` allows for the references on the other Sections.
      If `field_type` == 'embeddeddocument', `embedded_section` cannot be blank!
      It is equal to ListField(EmbeddedDocumentField(embedded_section.name)).
    """
    field_name = StringField(required=True, unique=True, help_text=_(u'Name'))
    field_type = StringField(required=True, help_text=_(u'Type'),
                             choices=FIELD_TYPE, default='string')
    embedded_section = ReferenceField('Section', help_text=_(u'Document type'))
    help_text = StringField(required=True, unique=True, help_text=_(u'Label'))
    default = DynamicField(help_text=_(u'Default value'))
    unique = BooleanField(required=True, default=False,
                          help_text=_(u'Unique values'))
    nullable = BooleanField(required=True, default=True,
                            help_text=_(u'This field can be Null'))
    blank = BooleanField(required=True, default=False,
                         help_text=_(u'This field can be blank'))
    readonly = BooleanField(required=True, default=False,
                            help_text=_(u'Read-only'))

    def clean(self):
        # Fill out `field_name` if not given
        if (self.field_name is None) or (self.field_name.strip() == ''):
            self.field_name = utils.slugify_downcode(self.help_text)

    def __unicode__(self):
        return u"%s (%s)" % (self.field_name, self.field_type)


class Section(TemplateGenericDocument):
    """
    Defines a section in the document that consists of fields,
    grouped by a similar subject.
    """
    help_text = StringField(required=True, help_text=_(u'Label'))
    description = StringField(help_text=_(u'Description'))
    fields = ListField(EmbeddedDocumentField(FieldDefinition),
                       help_text=_(u'Fields'))

    meta = {'collection': 'cms_section'}

    def save(self, *args, **kwargs):
        utils.FieldValidator().validate(self, ('fields',))

        super(Section, self).save(*args, **kwargs)
        

class SectionData(EmbeddedDocument):
    """
    Any additional data for any document that has `sections` attr.
    The schema is described in `section` attr.
    """
    data = ListField(DictField(), required=True, help_text=_(u'Data'))
    section = ReferenceField(Section, required=True,
                             help_text=_(u'Description'))


# END-USER DATA DOCUMENTS

# LIBRARY

class MediaLibrary(GenericDocument):
    """
    Tree structure: containers can reference to another containes,
    which means a folder in another folder.
    """
    is_file = BooleanField(required=True, default=True,
                           help_text=_(u'File'))
    mediafile = FileField(help_text=_(u'Media file'))
    thumbnail = ImageField(size=(100, 100, True), help_text=_(u'Thumbnail'))
    container = ReferenceField('MediaLibrary', reverse_delete_rule=CASCADE)
    container_safe = ReferenceField('MediaLibrary') # Safe link to a container:
                                                    # updated only when it's safe
                                                    # to update.
    meta = {
        'collection': 'media_library',
        'indexes': [
            {'fields': ('name', 'container', ), 'unique': True}
            ]
        }

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        if document.mediafile is not None:
            document.mediafile.delete()


    def save(self, force_insert=False, validate=True, 
             clean=True, write_concern=None, cascade=None, 
             cascade_kwargs=None, _refs=None, **kwargs):

        # No drafts in Media library.
        if self.status == 'draft':
            self.status = 'active'

        # Folders are not files.
        if not self.is_file:
            self.mediafile = None
            
        if self.container:

            # Can store elements in folders only.
            if self.container.is_file:
                self.container = self.container_safe # reverse change
                raise utils.WrongTypeError('cannot insert object into file!')

            # Destination container cannot be lower in the hierarchy of folders.
            # Check only for containers that already exist in the db.
            if (not self.is_file) and (self.id is not None):

                if self.higher_in_hierarchy(self, self.container):
                    self.container = self.container_safe # reverse change
                    raise utils.WrongDesctinationError(
                        'cannot insert object into this folder!')

            self.container_safe = self.container # solidify

        super(MediaLibrary, self).save(force_insert, validate, clean,
            write_concern, cascade, cascade_kwargs, _refs, **kwargs)

    @staticmethod
    def higher_in_hierarchy(document, container):
        """
        Recursively walks down, gathering folders in lower part of hierarchy,
        and then checks if `container` is among them.

        Makes sense only for existing folders. If `document` is a newly created
        folder, throws ValidationError.
        """
        def _collect_lower_level_containers(folder):
            """
            Recurse down through hierarchy to collect folders from lower levels.
            """
            children = folder.__class__.objects.filter(container=folder,
                                                       is_file=False)
            if children:
                lower_level_containers.extend(list(children))
                for child in children:
                    _collect_lower_level_containers(child)
            return

        lower_level_containers = list()
        _collect_lower_level_containers(document)

        return container in lower_level_containers


class EmbeddedGenericDocument(EmbeddedDocument):
    """
    Abstract class for all vocabulary-like embedded documents.
    """
    name = StringField(required=True, help_text=_(u'Name'))
    sections = ListField(EmbeddedDocumentField(SectionData),
                         help_text=_(u'Sections'))
    media = ListField(ReferenceField(MediaLibrary))

    meta = {'abstract': True}

    def save(self, *args, **kwargs):
        """
        Dummy save method to avoid 500 on POST or PATCH.
        """
        # Is it somehow possible to set `updated` and `updated_by`
        # in the master document from here?
        print args, kwargs
        for ii in dir(self.media): print ii
        pass

    def __unicode__(self):
        return self.name


class Voice(EmbeddedDocument):
    """
    Separate voice / instrument in the scores (either voice or instrument).
    """
    voice_type = StringField()
    voice_name = StringField()
    description = StringField()


class Piece(EmbeddedGenericDocument):
    """
    Musical piece.
    """
    author = ListField(StringField(), required=True, help_text=_(u'Author(s)'))
    voices = ListField(EmbeddedDocumentField(Voice), help_text=_(u'Voices'))
    incipit = StringField(help_text=_(u'Incipit'))
    scores_mxml = StringField(help_text=_(u'Original MusicXML'))
    scores_dict = DictField(help_text=_(u'Scores dictionary')) # converted from XML for indexing and searching by notes

    def save(self, *args, **kwargs):
        """
        Converts MusicXML to dictionary for indexing.
        """
        import xmltodict

        if (self.scores_dict is None) or (self.scores_dict == ''):
            try:
                self.scores_dict = xmltodict.parse(self.scores_mxml,
                                                   process_namespaces=True)
            except:
                # WARNING! This should raise a warning, not the error!
                pass

        super(Piece, self).save(*args, **kwargs)


class ManuscriptContent(EmbeddedGenericDocument):
    """
    Actual Manuscript content (scan parts and description).
    """
    page_description = StringField(help_text=_(u'Description'))


class Manuscript(GenericDocument):
    """
    Main container for manuscripts.
    """
    title = StringField(required=True, help_text=_(u'Title'))
    description = StringField(help_text=_(u'Description'))
    content = ListField(EmbeddedDocumentField(ManuscriptContent),
                        help_text=_(u'Content'))
    pieces = ListField(EmbeddedDocumentField(Piece), help_text=_(u'Pieces'))
    media = ListField(ReferenceField(MediaLibrary))

    def clean(self):
        utils.FieldValidator().validate(self, ('content',))


# SIGNALS

from mongoengine import signals

def create_api_key(sender, **kwargs):
    """
    Signal: automatic ApiKey creation for MongoUser.
    """
    if kwargs.get('created', False) is True:
        user = kwargs.get('document', None)
        user.set_api_key()
    

def control_permissions(sender, **kwargs):
    """
    Signal: check if there is no duplicates in permissions.
    """
    if kwargs.get('created', False) is True:
        document = kwargs.get('document', None)
        try:
            document.ensure_no_duplicates_permissions()
        except:
            pass # Do nothing.


signals.pre_delete.connect(MediaLibrary.pre_delete, sender=MediaLibrary)
