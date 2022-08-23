from datetime import datetime, timedelta
from jwt import encode
from django.conf import settings

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, CSRFCheck

from django.conf import settings
from django.contrib.auth import get_user_model

def generate_access_token(user):

    access_token_payload = {
        'user_id' : user.id,
        'exp' : datetime.utcnow() + timedelta(days=0, minutes=5),
        'iat' : datetime.utcnow(),
    }
    access_token = encode(
        access_token_payload, 
        settings.SECRET_KEY, 
        algorithm='HS256'
    ).decode('utf-8')

    return access_token


def generate_refresh_token(user):
    refresh_token_payload = {
        'user_id' : user.id,
        'exp' : datetime.utcnow() + timedelta(days=7),
        'iat' : datetime.utcnow()
    }
    refresh_token = encode(
        refresh_token_payload,
        settings.REFRESH_TOKEN_SECRET,
        algorithm='HS256'
    ).decode('utf-8')

    return refresh_token

        