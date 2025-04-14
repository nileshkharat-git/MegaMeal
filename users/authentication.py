from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

from users.models import ExpiringToken

class ExpiringTokenAuthentication(TokenAuthentication):
    model = ExpiringToken

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.select_related("user").get(key=key)
        
        except Exception as e:
            raise exceptions.AuthenticationFailed("Invalid token")
        
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted.')

        if token.is_expired:
            raise exceptions.AuthenticationFailed('Token has expired.')

        token.save()

        return (token.user, token)