from django.utils.translation import ugettext_lazy as _
from django.contrib.sessions.models import Session

from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from hymnbooks.apps.core import utils
from hymnbooks.apps.core.models import MongoUser, MongoGroup, \
     create_api_key, control_permissions

from mongoengine import signals

# Auto create API key when user is saved.
signals.post_save.connect(create_api_key, sender=MongoUser)

# Control permissions duplicates.
signals.post_save.connect(control_permissions, sender=MongoUser)
signals.post_save.connect(control_permissions, sender=MongoGroup)

# TEST
import inspect


class AppApiKeyAuthentication(ApiKeyAuthentication):
    """
    Authenticates everyone if the request is GET otherwise performs
    ApiKeyAuthentication.
    """
    def __init__(self, *args, **kwargs):
        self.super_self = super(AppApiKeyAuthentication, self)
        self.super_self.__init__(*args, **kwargs)

    def is_mongouser_authenticated(self, request):
        """
        Custom solution for MongoUser ApiKey authentication.
        ApiKey here is not a class (as it is realized in ORM approach),
        but a field MongoUser class.
        """
        try:
            username, api_key = self.super_self.extract_credentials(request)
        except ValueError:
            return self.super_self._unauthorized()

        if not username or not api_key:
            return self.super_self._unauthorized()

        lookup = {'username': username}
        try:
            user = MongoUser.objects.get(**lookup)
        except (MongoUser.DoesNotExist, MongoUser.MultipleObjectsReturned):
            return self.super_self._unauthorized()

        if not self.super_self.check_active(user):
            return False

        try:
            MongoUser.objects.get(username=username, api_key=api_key)
        except MongoUser.DoesNotExist:
            return self.super_self._unauthorized()

        request.user = user

        return True
    
    def is_authenticated(self, request, **kwargs):
        """
        Custom solution for `is_authenticated` function: MongoUsers has got
        authenticated through custom api_key check.
        """
        # print inspect.stack()[1][4], inspect.stack()[0][3]

        try:
            is_authenticated = self.super_self.is_authenticated(
                request, **kwargs)
        except TypeError as e:
            if "MongoUser" in str(e):
                is_authenticated = self.is_mongouser_authenticated(request)
            else:
                is_authenticated = False

        # Allow to see anything, AppAuthorization will take care of the rest.
        if request.method == 'GET':
            is_authenticated = True

        return is_authenticated

class CookieBasicAuthentication(BasicAuthentication):
    """
    If the user is already authenticated by a django session it will 
    allow the request (useful for ajax calls). If it is not, defaults
    to basic authentication, which other clients could use.
    """
    def __init__(self, *args, **kwargs):
        self.super_self = super(CookieBasicAuthentication, self)
        self.super_self.__init__(*args, **kwargs)

    def is_authenticated(self, request, **kwargs):
        if 'sessionid' in request.COOKIES:
            s = Session.objects.get(pk=request.COOKIES['sessionid'])
            if '_auth_user_id' in s.get_decoded():
                request.user = MongoUser.objects.get(
                    id=s.get_decoded()['_auth_user_id'])
                return True
        return self.super_self.is_authenticated(request, **kwargs)


class StaffAuthorization(Authorization):
    """
    Class for staff authorization.
    """
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        try:
            if bundle.request.user.is_superuser or bundle.request.user.is_staff:
                return object_list.all()
            else:
                return []
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))
        
    def read_detail(self, object_list, bundle):        
        try:
            return bundle.request.user.is_superuser or bundle.request.user.is_staff
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def create_list(self, object_list, bundle):
        try:
            if bundle.request.user.is_superuser or bundle.request.user.is_staff:
                return object_list
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def create_detail(self, object_list, bundle):
        try:
            return bundle.request.user.is_superuser or bundle.request.user.is_staff
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def update_detail(self, object_list, bundle):
        try:
            return bundle.request.user.is_superuser or bundle.request.user.is_staff
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def update_list(self, object_list, bundle):
        try:
            if bundle.request.user.is_superuser or bundle.request.user.is_staff:
                return object_list
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def delete_list(self, object_list, bundle):
        """
        Only superuser can delete lists!
        """
        try:
            if bundle.request.user.is_superuser or bundle.request.user.is_staff:
                return object_list
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def delete_detail(self, object_list, bundle):
        """
        If user has permissions to delete detail, it can only 
        delete those ctreated by him.
        """
        try:
            return bundle.request.user.is_superuser or bundle.request.user.is_staff
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))


class AppAuthorization(Authorization):
    """
    Custom authorization using permissions only:

    * Updates and deletes allowed to superuser

    * In other cases, even if User has permissions on a particular
      document_type, he can only update and delete his documents.
    """    
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        user = bundle.request.user
        document_type = object_list._document._class_name
        try:
            if user.is_superuser or user.is_staff:
                return object_list.all()
            elif user.has_permission('read_list', document_type):
                return object_list.filter(created_by__exact=user)
            else:
                return []
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))
        
    def read_detail(self, object_list, bundle):
        return bundle.request.user.is_superuser or \
          bundle.request.user.has_permission('read_detail',
                                             bundle.obj._class_name)

    def create_detail(self, object_list, bundle):
        try:
            return bundle.request.user.is_superuser \
              or bundle.request.user.has_permission('create_detail',
                                                    bundle.obj._class_name)
        except AttributeError:
            raise Unauthorized(_('You have to authenticate first!'))

    def create_list(self, object_list, bundle):
        return object_list

    def update_detail(self, object_list, bundle):
        return bundle.request.user.is_superuser or \
          (bundle.request.user.has_permission('update_detail',
                                              bundle.obj._class_name)
              and bundle.obj.created_by == bundle.request.user)

    def update_list(self, object_list, bundle):
        allowed = []

        # Since they may not all be saved, iterate over them.
        for obj in object_list:
            if self.update_detail([obj], bundle):
                allowed.append(obj)

        return allowed

    def delete_list(self, object_list, bundle):
        """
        Only superuser can delete lists!
        """
        if self.bundle.request.user.is_superuser:
            return True

        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        """
        If user has permissions to delete detail, it can only 
        delete those ctreated by him.
        """
        if bundle.request.user.is_superuser:
            return True

        if bundle.request.user.has_permission('delete_detail',
                                              object_list._document._class_name):
            return bundle.obj.created_by == bundle.request.user

        raise Unauthorized("Sorry, no deletes.")


class AnyoneCanViewAuthorization(AppAuthorization):
    """
    Custom authorization for documents that can be viewed by anyone,
    but require Authentification and Authorization for updates.
    """
    def read_list(self, object_list, bundle):
        return object_list.all()

    def read_detail(self, object_list, bundle):
        return True
