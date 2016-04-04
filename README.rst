django-edx-courseware
=====================

API endpoint to get enrolled student's progress and some course details for requested course


Get Going
---------

Clone this repository and install django-edx-courseware with command

    python setup.py install

Add 'django-edx-courseware' to installed apps in lms/envs/common.py

Add packages url to lms/urls.py

    url(r'^custom_api/', include('django-edx-courseware.urls')),

Dependancies
------------

    Django >= 1.7