import os
import tempfile
import shutil

from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.conf import settings
from movies import tasks as tasks_module
from movies.models import Movie
from movies.tasks import (
    save_converted_resolution,
    save_thumbnail,
    save_trailer,
    save_video_duration,
    finalize_conversion,
)
from movies.utils.video import (
    convert_video_to_resolution,
    generate_thumbnail,
    cut_video_for_trailer,
    get_video_duration,
)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MovieTasksTest(TestCase):
    def setUp(self):
        self.tmp_media = settings.MEDIA_ROOT
        os.makedirs(self.tmp_media, exist_ok=True)
        self.source_path = os.path.join(self.tmp_media, "original.mp4")
        with open(self.source_path, "wb") as f:
            f.write(b"fake video data")
        self.movie = Movie.objects.create(title="TestMovie")
        with open(self.source_path, "rb") as f:
            self.movie.video_file.save("original.mp4", ContentFile(f.read()), save=True)
    def tearDown(self):
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_save_converted_resolution_updates_field(self):
        def fake_convert(src, res):
            target = os.path.join(self.tmp_media, f"vid_{res}.mp4")
            with open(target, "wb") as f:
                f.write(b"converted")
            return target
        real_convert = tasks_module.convert_video_to_resolution
        try:
            tasks_module.convert_video_to_resolution = fake_convert
            save_converted_resolution(self.source_path, self.movie.id, 360)
            m = Movie.objects.get(pk=self.movie.id)
            self.assertTrue(m.video_360p.name.endswith("vid_360.mp4"))
            self.assertTrue(
                os.path.exists(os.path.join(self.tmp_media, m.video_360p.name))
            )
        finally:
            tasks_module.convert_video_to_resolution = real_convert

    def test_save_thumbnail_creates_file_and_updates_field(self):
        def fake_generate(src, dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(b"thumb")

        real_generate = tasks_module.generate_thumbnail
        try:
            tasks_module.generate_thumbnail = fake_generate
            save_thumbnail(self.movie.id, self.source_path)
            m = Movie.objects.get(pk=self.movie.id)
            self.assertTrue(m.thumbnail.name.endswith("TestMovie_thumb.webp"))
            self.assertTrue(os.path.exists(os.path.join(self.tmp_media, m.thumbnail.name)))
        finally:
            tasks_module.generate_thumbnail = real_generate

    def test_save_trailer_creates_file_and_updates_field(self):
        def fake_cut(src, dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(b"trailer")
        real_cut = tasks_module.cut_video_for_trailer
        try:
            tasks_module.cut_video_for_trailer = fake_cut

            save_trailer(self.movie.id, self.source_path)

            m = Movie.objects.get(pk=self.movie.id)
            self.assertTrue(m.trailer.name.endswith("TestMovie_trailer.mp4"))
            self.assertTrue(os.path.exists(os.path.join(self.tmp_media, m.trailer.name)))
        finally:
            tasks_module.cut_video_for_trailer = real_cut

    def test_save_video_duration_sets_duration(self):
        def fake_duration(src):
            return 123
        real_get_duration = tasks_module.get_video_duration
        try:
            tasks_module.get_video_duration = fake_duration

            save_video_duration(self.movie.id, self.source_path)

            m = Movie.objects.get(pk=self.movie.id)
            self.assertEqual(m.duration, 123)
        finally:
            tasks_module.get_video_duration = real_get_duration

    def test_finalize_conversion_deletes_original_and_clears_field(self):
        m = Movie.objects.get(pk=self.movie.id)
        orig_path = m.video_file.path
        self.assertTrue(os.path.exists(orig_path))
        finalize_conversion(orig_path, self.movie.id)
        self.assertFalse(os.path.exists(orig_path))
        m.refresh_from_db()
        self.assertFalse(m.video_file)