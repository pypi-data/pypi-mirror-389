# Django REST Framework extensions by Amsterdam Datapunt


Extensions to Django REST Framework by Amsterdam Datapunt. Amsterdam Datapunt
provides access to municipal data through, at times, public APIs. This project
provides some basic classes and instructions to set the behavior
of Django REST Framework API to the standards of Amsterdam Datapunt.

## Installation instructions

Given that you have a Django project that generates a REST API using Django
REST Framework:

```shell
pip install drf_amsterdam
```

To use the API page styling provided by this package, you need to add datapunt_api to the INSTALLED_APPS list in your Django settings file — before 'rest_framework'.
This ensures that the templates and static files included in datapunt_api override those provided by Django REST Framework, so the custom styling is applied correctly.


## Building and running the application

If you want to use this package in a local project setup:

```shell
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

> **Note**: This package itself is not a standalone application, but is designed to be integrated into an existing Django project.


## Running tests

Run the tests in a virtualenv and run the script runtests.py from project root.

requirements: spatialite, sqlite extension

or use docker-compose:

```shell
docker compose build
docker compose run --rm tests pytest --cov
```

## Changelog

### 1.0.0
- Added types
- Tidied up code
- Added tests to reach 100% code coverage

#### Breaking changes
- `LinksField` now extends `RelatedField` instead of `HyperLinkedIdentityField`. The reason for this is that
`HyperLinkedIdentityField` has to return a `HyperLink` object in order to comply with the rules of covariance,
which is not what we desire it to return.
