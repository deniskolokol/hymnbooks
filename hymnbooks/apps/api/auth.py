from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from mongoengine import signals

from hymnbooks.apps.core import utils
from hymnbooks.apps.core.models import MongoUser, create_api_key


# Auto create API key when user is saved.
signals.post_save.connect(create_api_key, sender=MongoUser)


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

        # Run authentication first (even if it's GET, 
        # user will be used by AppAuthorization)
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


class AppAuthorization(Authorization):
    """
    Custom authorization using permissions.
    """
    def __init__(self, *args, **kwargs):
        """
        Warning! Dummy for the development period!
        Delete after testing.
        """
        super(AppAuthorization, self).__init__(*args, **kwargs)

    def create_detail(self, object_list, bundle):
        print bundle.obj, type(bundle.obj)
        return True
        # return bundle.obj.created_by == bundle.request.user

    # def create_list(self, object_list, bundle):
    #     # Create list is auto-assigned to ``user``.
    #     return object_list

    # def read_list(self, object_list, bundle):
    #     # This assumes a ``QuerySet`` from ``ModelResource``.
    #     return object_list.filter(created_by=bundle.request.user)

    # def read_detail(self, object_list, bundle):
    #     # Is the requested object owned by the user?
    #     return bundle.obj.created_by == bundle.request.user

    # def update_list(self, object_list, bundle):
    #     allowed = []

    #     # Since they may not all be saved, iterate over them.
    #     for obj in object_list:
    #         if obj.user == bundle.request.user:
    #             allowed.append(obj)

    #     return allowed

    # def update_detail(self, object_list, bundle):
    #     return bundle.obj.user == bundle.request.user

    # def delete_list(self, object_list, bundle):
    #     # Sorry user, no deletes for you!
    #     raise Unauthorized("Sorry, no deletes.")

    # def delete_detail(self, object_list, bundle):
    #     raise Unauthorized("Sorry, no deletes.")
