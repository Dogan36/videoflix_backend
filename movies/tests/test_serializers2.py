import io
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from movies.models import Movie, MovieProgress, Category
from movies.serializers import MovieSerializer, MovieFileSerializer, MovieProgressSerializer

User = get_user_model()

class MovieSerializerAdditionalTests(TestCase):
    def setUp(self):
        # create user, categories, movie and progress
        self.user = User.objects.create_user(email="u@example.com", password="pass")
        self.cat1 = Category.objects.create(name="Action")
        self.cat2 = Category.objects.create(name="Drama")
        self.movie = Movie.objects.create(title="Test", description="Desc")
        self.movie.categories.set([self.cat1, self.cat2])
        # play progress
        self.progress = MovieProgress.objects.create(
            user=self.user, movie=self.movie,
            progressInSeconds=42, finished=True
        )
        self.factory = RequestFactory()

    def test_progress_field_unauthenticated(self):
        req = self.factory.get("/")
        # no user on request → progress == None
        req.user = type("Anon", (), {"is_authenticated": False})
        data = MovieSerializer(self.movie, context={"request": req}).data
        self.assertIsNone(data["progress"])

    def test_progress_field_authenticated(self):
        req = self.factory.get("/")
        req.user = self.user
        data = MovieSerializer(self.movie, context={"request": req}).data
        self.assertIn("progressInSeconds", data["progress"])
        self.assertEqual(data["progress"]["progressInSeconds"], 42)

    def test_categories_listed(self):
        req = self.factory.get("/")
        req.user = self.user
        data = MovieSerializer(self.movie, context={"request": req}).data
        # categories come back as IDs
        self.assertCountEqual(data["categories"], [self.cat1.id, self.cat2.id])


class MovieFileSerializerAdditionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u2@example.com", password="pass")
        self.movie = Movie.objects.create(title="FileTest")
        self.progress = MovieProgress.objects.create(
            user=self.user, movie=self.movie,
            progressInSeconds=7, finished=False
        )
        self.factory = RequestFactory()

    def test_progressInSeconds_and_finished_fields(self):
        req = self.factory.get("/")
        req.user = self.user
        ser = MovieFileSerializer(self.movie, context={"request": req})
        data = ser.data
        # default resolution fields present
        self.assertIn("video_120p", data)
        # progressInSeconds and finished come from MovieProgress
        self.assertEqual(data["progressInSeconds"], 7)
        self.assertFalse(data["finished"])

    def test_progressInSeconds_defaults_to_zero(self):
        # no progress entry for new movie
        other = Movie.objects.create(title="NoProg")
        req = self.factory.get("/")
        req.user = self.user
        data = MovieFileSerializer(other, context={"request": req}).data
        self.assertEqual(data["progressInSeconds"], 0)
        self.assertFalse(data["finished"])


class MovieProgressSerializerAdditionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u3@example.com", password="pass")
        self.movie = Movie.objects.create(title="ProgTest")
        self.factory = RequestFactory()

    def test_create_new_progress(self):
        req = self.factory.post("/")
        req.user = self.user
        payload = {"movie_id": self.movie.id, "progressInSeconds": 5, "finished": True}
        ser = MovieProgressSerializer(data=payload, context={"request": req})
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()
        self.assertEqual(obj.progressInSeconds, 5)
        self.assertTrue(obj.finished)

    def test_update_existing_progress(self):
        MovieProgress.objects.create(user=self.user, movie=self.movie, progressInSeconds=1, finished=False)
        req = self.factory.post("/")
        req.user = self.user
        payload = {"movie_id": self.movie.id, "progressInSeconds": 99, "finished": True}
        ser = MovieProgressSerializer(data=payload, context={"request": req})
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()
        self.assertEqual(MovieProgress.objects.count(), 1)
        self.assertEqual(obj.progressInSeconds, 99)
        self.assertTrue(obj.finished)