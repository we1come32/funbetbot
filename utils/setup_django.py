import os
import loguru

import django.conf
from django.core.wsgi import get_wsgi_application


django.conf.ENVIRONMENT_VARIABLE = 'TGBetBot'
os.environ.setdefault('TGBetBot', "django_project.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

application = loguru.logger.catch(get_wsgi_application)()
