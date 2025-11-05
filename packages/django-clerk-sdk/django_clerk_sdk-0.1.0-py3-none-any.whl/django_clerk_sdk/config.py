from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import gettext_lazy as _


class DjangoClerkSDKConfig(DjangoAppConfig):
    name = 'django_clerk_sdk'
    
