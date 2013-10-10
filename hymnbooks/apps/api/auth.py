from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication

from mongoengine import signals

from hymnbooks.apps.core import models, utils


# Auto create API key when user is saved.
signals.post_save.connect(models.create_api_key, sender=models.MongoUser)


class AppApiKeyAuthentication(ApiKeyAuthentication):
    """
    Authenticates everyone if the request is GET otherwise performs
    ApiKeyAuthentication.
    """
    def is_mongouser_authenticated(self, request):
        """
        Custom solution for MongoUser ApiKey authentication.
        ApiKey here is not a class (as it is realized in ORM approach),
        but a field MongoUser class.
        """
        username, api_key = super(AppApiKeyAuthentication,
                                  self).extract_credentials(request)
        try:
            models.MongoUser.objects.get(username=username, api_key=api_key)
        except models.MongoUser.DoesNotExist:
            return False

        return True
    
    def is_authenticated(self, request, **kwargs):
        """
        Custom solution for `is_authenticated` function: MongoUsers has got
        authenticated through custom api_key check.
        """
        if request.method == 'GET':
            return True
        try:
            is_authenticated = super(AppApiKeyAuthentication,
                                     self).is_authenticated(request, **kwargs)
        except TypeError as e:
            if "MongoUser" in str(e):
                is_authenticated = self.is_mongouser_authenticated(request)
            else:
                is_authenticated = False
        return is_authenticated


class AppAuthorization(Authorization):
    """
    Custom authorization using permissions.
    """
    def __init__(self, *args, **kwargs):
        super(AppAuthorization, self).__init__(*args, **kwargs)
