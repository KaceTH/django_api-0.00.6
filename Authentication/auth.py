from jwt import decode, ExpiredSignatureError
from rest_framework.authentication import BaseAuthentication
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from django.conf import settings
from .models import User


class SafeAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try :
            access_token = authorization_header.split(' ')[1]
            payload = decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
        except ExpiredSignatureError :
            raise exceptions.AuthenticationFailed('access_token expire')
        except IndexError :
            exceptions.AuthenticationFailed('Token prefix missing')

        user = User.objects.filter(id=payload['user_id']).first()
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('user is inactive')
        return (user, None)

