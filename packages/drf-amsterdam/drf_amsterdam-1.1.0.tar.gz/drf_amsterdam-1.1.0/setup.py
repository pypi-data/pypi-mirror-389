import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='drf_amsterdam',
    version='1.1.0',
    packages=find_packages(),
    install_requires=[
        'djangorestframework',
        'drf_extensions',
        'djangorestframework_csv',
        'djangorestframework_xml'],
    include_package_data=True,
    package_data={'datapunt_api': ['py.typed']},
    license='Mozilla Public License Version 2.0',
    description='Amsterdam Datapunt code and style for Django REST Framework.',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Amsterdam Datapunt',
    author_email='datapunt@amsterdam.nl',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)'
    ],
)
