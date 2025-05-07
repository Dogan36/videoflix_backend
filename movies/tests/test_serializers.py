from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

from movies.models import Movie, Category
from movies.serializers import MovieSerializer

User = get_user_model()

class MovieSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='pass')
        self.request = self._create_request(self.user)

        self.cat1, self.cat2 = self._create_test_categories()
        self.movie = self._create_test_movie()

    def _create_request(self, user):
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        return request

    def _create_test_categories(self):
        cat1 = Category.objects.create(name="Action")
        cat2 = Category.objects.create(name="Comedy")
        return cat1, cat2

    def _create_test_movie(self):
        movie = Movie.objects.create(
            title="Test Movie",
            description="A movie for testing.",
            duration=123,
        )
        movie.categories.add(self.cat1, self.cat2)
        self._attach_files_to_movie(movie)
        return movie

    def _attach_files_to_movie(self, movie):
        thumb = self._create_uploaded_file("thumb.jpg", b"thumbcontent", "image/jpeg")
        trailer = self._create_uploaded_file("trailer.mp4", b"videocontent", "video/mp4")
        movie.thumbnail.save("thumb.jpg", thumb, save=True)
        movie.trailer.save("trailer.mp4", trailer, save=True)

    def _create_uploaded_file(self, name, content, content_type):
        return SimpleUploadedFile(name=name, content=content, content_type=content_type)

    def test_serialized_fields_exist(self):
        serializer = MovieSerializer(self.movie, context={'request': self.request})
        data = serializer.data
        # Stelle sicher, dass die wichtigsten Felder serialisiert werden
        expected_fields = {'id', 'title', 'description', 'thumbnail', 'trailer', 'categories', 'progress'}
        self.assertTrue(expected_fields.issubset(set(data.keys())))

    def test_field_values_match_model(self):
        serializer = MovieSerializer(self.movie, context={'request': self.request})
        data = serializer.data
        # Nur die tatsächlich serialisierten Felder prüfen
        self.assertEqual(data['title'], self.movie.title)
        self.assertEqual(data['description'], self.movie.description)
        # Kategorien-Liste prüft IDs
        cats = data['categories']
        expected_ids = [self.cat1.id, self.cat2.id]
        self.assertCountEqual(cats, expected_ids)

    def test_file_fields_are_serialized_with_url(self):
        serializer = MovieSerializer(self.movie, context={'request': self.request})
        data = serializer.data
        thumb_url = data['thumbnail']
        trailer_url = data['trailer']
        self.assertIsInstance(thumb_url, str)
        self.assertTrue(len(thumb_url) > 0)
        self.assertIsInstance(trailer_url, str)
        self.assertTrue(len(trailer_url) > 0)
