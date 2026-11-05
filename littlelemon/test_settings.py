"""Explicit SQLite-only fallback for tests without a MySQL service."""
import os
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-only-key-never-use-in-deployment')
os.environ.setdefault('DJANGO_DEBUG', 'True')
from .settings import *  # noqa: F403
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}  # noqa: F405
