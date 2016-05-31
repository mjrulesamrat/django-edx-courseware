import os
from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}

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
    package_data=package_data("django-edx-courseware", []),
)