from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from movies.models import Movie, Category, MovieProgress

User = get_user_model()

class MovieViewsTest(APITestCase):
    def setUp(self):
        # Create and authenticate user
        self.user = User.objects.create_user(email='user@example.com', password='pass', is_active=True)
        self.token, _ = Token.objects.get_or_create(user=self.user)
        # Create categories
        self.cat1 = Category.objects.create(name='Action')
        self.cat2 = Category.objects.create(name='Drama')
        # Create movies
        for i in range(5):
            m = Movie.objects.create(title=f'Movie{i}', description='desc')
            m.categories.set([self.cat1, self.cat2])
        # Create progress entries: only for first two movies
        for idx, movie in enumerate(Movie.objects.all()[:2]):
            MovieProgress.objects.create(user=self.user, movie=movie, progressInSeconds=10*idx, finished=False)
        self.home_url = '/movies/home/'
        self.loadmore_url = '/movies/load-more/'

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_home_requires_auth(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_home_requires_auth(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_home_returns_expected_structure(self):
        self.authenticate()
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Keys at top-level
        self.assertIn('newest', data)
        self.assertIn('recently_watched', data)
        self.assertIn('finished', data)
        self.assertIn('categories', data)
                # Paginated structure for 'newest'
        newest_page = data['newest']
        self.assertIn('results', newest_page)
        self.assertIn('next', newest_page)
        # No 'previous' or 'count' in home summary endpoint
        # Default page_size=5, we created 5 movies
        self.assertEqual(len(newest_page['results']), 5)
        self.assertEqual(len(newest_page['results']), 5)
        # recently_watched
        recent_page = data['recently_watched']
        self.assertIn('results', recent_page)
        self.assertEqual(len(recent_page['results']), 2)
        # finished none
        finished_page = data['finished']
        self.assertIn('results', finished_page)
        self.assertEqual(len(finished_page['results']), 0)
        # categories for each category
        self.assertTrue(isinstance(data['categories'], list))
        # Each category object has category and paginated results
        for cat in data['categories']:
            self.assertIn('category', cat)
            self.assertIn('category_id', cat)
            self.assertIn('results', cat)
            self.assertIn('next', cat)

    def test_home_pagination_page_size(self):
        self.authenticate()
        # limit to 3
        response = self.client.get(self.home_url, {'page_size': 3})
        data = response.json()
        newest_page = data['newest']
        self.assertEqual(len(newest_page['results']), 3)

        self.authenticate()
        # limit to 3
        response = self.client.get(self.home_url, {'page_size': 3})
        data = response.json()
        self.assertEqual(len(data['newest']['results']), 3)

    def test_load_more_newest(self):
        self.authenticate()
        # request first page size=2
        response = self.client.get(self.loadmore_url, {'section': 'newest', 'page': 1, 'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)
        # next link present when more
        self.assertIn('next', data)
        self.assertIsNotNone(data['next'])

    def test_load_more_recently_watched(self):
        self.authenticate()
        response = self.client.get(self.loadmore_url, {'section':'recently_watched','page':1,'page_size':2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn('results', payload)
        self.assertEqual(len(payload['results']), 2)
        self.assertIn('next', payload)

    def test_load_more_finished(self):
        self.authenticate()
        response = self.client.get(self.loadmore_url, {'section':'finished','page':1,'page_size':2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn('results', payload)
        # no progress entries marked finished, so should be empty
        self.assertEqual(len(payload['results']), 0)
        self.assertIsNone(payload.get('next'))

    def test_load_more_category(self):
        self.authenticate()
        response = self.client.get(self.loadmore_url, {'section':'category','category_id':self.cat1.id,'page':1,'page_size':10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload['results']), 5)

    def test_load_more_requires_section(self):
        self.authenticate()
        response = self.client.get(self.loadmore_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['results'], [])
        self.authenticate()
        response = self.client.get(self.loadmore_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['results'], [])
        
    def test_load_more_requires_auth(self):
        """Ensure load-more endpoint requires authentication"""
        response = self.client.get(self.loadmore_url, {'section': 'newest'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_load_more_unknown_section(self):
        """Unknown section should return empty results"""
        self.authenticate()
        response = self.client.get(self.loadmore_url, {'section': 'unknown', 'page': 1, 'page_size': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['results'], [])
        self.assertIsNone(payload.get('next'))

    def test_load_more_invalid_category(self):
        """Invalid category_id should return empty results"""
        self.authenticate()
        response = self.client.get(self.loadmore_url, {'section': 'category', 'category_id': 999, 'page': 1, 'page_size': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['results'], [])
        self.assertIsNone(payload.get('next'))