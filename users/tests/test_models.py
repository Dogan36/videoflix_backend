from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

from movies.models import Movie, Category
from movies.serializers import MovieSerializer

User = get_user_model()

class MovieSerializerTest(TestCase):
    def setUp(self):
        # Benutzer für Request-Kontext
        self.user = User.objects.create_user(email='u@example.com', password='pass')
        factory = APIRequestFactory()
        self.request = factory.get('/')
        self.request.user = self.user

        # Kategorien erstellen
        self.cat1 = Category.objects.create(name="Action")
        self.cat2 = Category.objects.create(name="Comedy")
        # Movie erstellen
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="A movie for testing.",
            duration=123,
        )
        self.movie.categories.add(self.cat1, self.cat2)
        # Thumbnail und Trailer simulieren
        thumb = SimpleUploadedFile(
            name="thumb.jpg", content=b"thumbcontent", content_type="image/jpeg"
        )
        trailer = SimpleUploadedFile(
            name="trailer.mp4", content=b"videocontent", content_type="video/mp4"
        )
        self.movie.thumbnail.save("thumb.jpg", thumb, save=True)
        self.movie.trailer.save("trailer.mp4", trailer, save=True)

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
