from django.test import TestCase
from rest_framework.test import APIClient

from datapunt_api.pagination import HALCursorPagination
from tests.models import Person
from tests.views import PersonViewSet


class HALPaginationTest(TestCase):
    def setUp(self):
        for x in range(10):
            person = Person()
            person.name = f'person #{x}'
            person.save()

    def test_pagination_one_page(self):
        client = APIClient()
        response = client.get('/tests/person/?page_size=10', format='json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIsNone(payload['_links']['previous']['href'])
        self.assertIsNone(payload['_links']['next']['href'])

        self.assertEqual(payload['count'], 10)
        self.assertEqual(len(payload['results']), 10)

    def test_pagination_multiple_pages(self):
        client = APIClient()
        response = client.get('/tests/person/?page_size=2&page=2', format='json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIsNotNone(payload['_links']['previous']['href'])
        self.assertEqual(payload['_links']['previous']['href'],
                         'http://testserver/tests/person/?page=1&page_size=2')

        self.assertIsNotNone(payload['_links']['next']['href'])
        self.assertEqual(payload['_links']['next']['href'],
                         'http://testserver/tests/person/?page=3&page_size=2')

        self.assertEqual(payload['count'], 10)
        self.assertEqual(len(payload['results']), 2)

    def test_pagination_url_endswith_api(self):
        client = APIClient()
        response = client.get('/tests/person.api', format='json')

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['_links']['self']['href'], 'http://testserver/tests/person.api')
        self.assertEqual(response.data['_links']['self']['href'], 'http://testserver/tests/person')


class HALCursorPaginationTest(TestCase):
    def setUp(self):
        setattr(PersonViewSet, 'pagination_class', HALCursorPagination)
        setattr(HALCursorPagination, 'ordering', ['id'])

        for x in range(10):
            person = Person()
            person.name = f'person #{x}'
            person.save()

    def test_pagination_one_page(self):
        client = APIClient()
        response = client.get('/tests/person/?page_size=10', format='json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIsNone(payload['_links']['previous']['href'])
        self.assertIsNone(payload['_links']['next']['href'])

        self.assertEqual(payload['count'], 10)
        self.assertEqual(len(payload['results']), 10)

    def test_pagination_multiple_pages(self):
        client = APIClient()
        response = client.get('/tests/person/?page_size=2', format='json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIsNone(payload['_links']['previous']['href'])
        self.assertIsNotNone(payload['_links']['next']['href'])
        self.assertIn('cursor=', payload['_links']['next']['href'])

        self.assertEqual(payload['count'], 10)
        self.assertEqual(len(payload['results']), 2)

    def test_pagination_without_count(self):
        setattr(HALCursorPagination, 'count_table', False)

        client = APIClient()
        response = client.get('/tests/person/?page_size=10', format='json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertNotIn('count', payload)
        self.assertEqual(len(payload['results']), 10)
