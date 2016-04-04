__author__ = 'Jay Modi'

from django.conf import settings
from django.conf.urls import patterns, include, url

from .views import course_data

urlpatterns = [
    url(
        r'^courses-data/{}$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        course_data,
        name='edx_course_progress',
    ),
]
