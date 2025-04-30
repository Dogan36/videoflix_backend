from django.test import TestCase
from django.contrib.auth import get_user_model
from movies.models import Movie, MovieProgress
from django.utils import timezone
import time

User = get_user_model()

class MovieModelTest(TestCase):
    def test_str_returns_title(self):
        m = Movie.objects.create(title="My Movie")
        self.assertEqual(str(m), "My Movie")

    def test_default_conversion_started(self):
        m = Movie.objects.create(title="Foo")
        self.assertFalse(m.conversion_started)
        # created_at ist in der Vergangenheit (nahe jetzt)
        self.assertTrue(timezone.now() >= m.created_at)

class MovieProgressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@example.com", password="pass")
        self.movie = Movie.objects.create(title="Bar")

    def test_unique_constraint(self):
        MovieProgress.objects.create(user=self.user, movie=self.movie)
        with self.assertRaises(Exception):
            # Ein zweiter Eintrag für denselben User/Movie muss scheitern
            MovieProgress.objects.create(user=self.user, movie=self.movie)

    def test_updated_at_changes_on_save(self):
        prog = MovieProgress.objects.create(user=self.user, movie=self.movie, progressInSeconds=10)
        old = prog.updated_at
        time.sleep(0.01)
        prog.progressInSeconds = 20
        prog.save()
        self.assertTrue(prog.updated_at > old)

    def test_str_format(self):
        prog = MovieProgress.objects.create(
            user=self.user,
            movie=self.movie,
            progressInSeconds=30
        )
        # … dann progress-Feld setzen und speichern
        prog.progress = "50%"
        prog.save()