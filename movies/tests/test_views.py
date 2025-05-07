from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from movies.models import Movie, Category, MovieProgress

User = get_user_model()

class MovieViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='pass', is_active=True)
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.cat1 = Category.objects.create(name='Action')
        self.cat2 = Category.objects.create(name='Drama')
        for i in range(5):
            m = Movie.objects.create(title=f'Movie{i}', description='desc')
            m.categories.set([self.cat1, self.cat2])
        for idx, movie in enumerate(Movie.objects.all()[:2]):
            MovieProgress.objects.create(user=self.user, movie=movie, progressInSeconds=10 * idx, finished=False)
        self.home_url = '/movies/home/'
        self.loadmore_url = '/movies/load-more/'

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def assert_paginated_section(self, section, expected_length=None):
        self.assertIn('results', section)
        self.assertIn('next', section)
        if expected_length is not None:
            self.assertEqual(len(section['results']), expected_length)

    def assert_standard_response(self, response, expected_status=status.HTTP_200_OK):
        self.assertEqual(response.status_code, expected_status)
        return response.json()

    def test_home_requires_auth(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_home_returns_expected_structure(self):
        self.authenticate()
        data = self.assert_standard_response(self.client.get(self.home_url))
        for key in ['newest', 'recently_watched', 'finished', 'categories']:
            self.assertIn(key, data)
        self.assert_paginated_section(data['newest'], expected_length=5)
        self.assert_paginated_section(data['recently_watched'], expected_length=2)
        self.assert_paginated_section(data['finished'], expected_length=0)
        self.assertIsInstance(data['categories'], list)
        for cat in data['categories']:
            for key in ['category', 'category_id', 'results', 'next']:
                self.assertIn(key, cat)

    def test_home_pagination_page_size(self):
        self.authenticate()
        data = self.assert_standard_response(self.client.get(self.home_url, {'page_size': 3}))
        self.assertEqual(len(data['newest']['results']), 3)

    def _load_more_and_check(self, params, expected_len, expect_next=True):
        self.authenticate()
        data = self.assert_standard_response(self.client.get(self.loadmore_url, params))
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), expected_len)
        if expect_next:
            self.assertIn('next', data)
        else:
            self.assertIsNone(data.get('next'))

    def test_load_more_newest(self):
        self._load_more_and_check({'section': 'newest', 'page': 1, 'page_size': 2}, expected_len=2)

    def test_load_more_recently_watched(self):
        self._load_more_and_check({'section': 'recently_watched', 'page': 1, 'page_size': 2}, expected_len=2)

    def test_load_more_finished(self):
        self._load_more_and_check({'section': 'finished', 'page': 1, 'page_size': 2}, expected_len=0, expect_next=False)

    def test_load_more_category(self):
        self._load_more_and_check({
            'section': 'category',
            'category_id': self.cat1.id,
            'page': 1,
            'page_size': 10
        }, expected_len=5)

    def test_load_more_requires_section(self):
        self._load_more_and_check({}, expected_len=0, expect_next=False)

    def test_load_more_requires_auth(self):
        response = self.client.get(self.loadmore_url, {'section': 'newest'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_load_more_unknown_section(self):
        self._load_more_and_check({'section': 'unknown', 'page': 1, 'page_size': 5}, expected_len=0, expect_next=False)

    def test_load_more_invalid_category(self):
        self._load_more_and_check({
            'section': 'category',
            'category_id': 999,
            'page': 1,
            'page_size': 5
        }, expected_len=0, expect_next=False)
