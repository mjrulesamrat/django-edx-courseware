import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-edx-courseware',
    version='0.1',
    packages=['django-edx-courseware'],
    include_package_data=True,
    license='MIT License', 
    description='A simple Django app to serve edx courseware data through API call',
    long_description=README,
    url='http://github.com/mjrulesamrat',
    author='Jay Modi',
    author_email='mjrulesamrat@gmail.com',
)