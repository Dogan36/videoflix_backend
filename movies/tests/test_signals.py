import os
import shutil
import tempfile
from unittest import mock
from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from movies.models import Movie
from movies.tasks import save_converted_resolution, save_thumbnail, save_trailer, save_video_duration, finalize_conversion
import django_rq

class SignalTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._orig_media_root = settings.MEDIA_ROOT
        cls.tmp_media = tempfile.mkdtemp()
        settings.MEDIA_ROOT = cls.tmp_media

    @classmethod
    def tearDownClass(cls):
        settings.MEDIA_ROOT = cls._orig_media_root
        shutil.rmtree(cls.tmp_media)
        super().tearDownClass()

    def setUp(self):
        video_content = b'video content'
        self.video_file = SimpleUploadedFile('test.mp4', video_content, content_type='video/mp4')
        self.movie = Movie.objects.create(
            title='Test Movie',
            video_file=self.video_file,
            conversion_started=False
        )

    @mock.patch('movies.signals.wait_until_file_is_ready', return_value=True)
    @mock.patch('django_rq.get_queue')
    def test_video_post_save_enqueues_all_tasks(self, mock_get_queue, mock_wait):
        fake_queue = mock.Mock()
        mock_get_queue.return_value = fake_queue

        # Trigger post_save
        self.movie.conversion_started = False
        self.movie.save(update_fields=['conversion_started'])

        # Flag set
        m = Movie.objects.get(pk=self.movie.pk)
        self.assertTrue(m.conversion_started)

        # Check conversion tasks
        expected_calls = [
            mock.call(save_converted_resolution, mock.ANY, self.movie.pk, res)
            for res in [120, 360, 720, 1080]
        ] + [
            mock.call(save_thumbnail, self.movie.pk, mock.ANY),
            mock.call(save_trailer, self.movie.pk, mock.ANY),
            mock.call(save_video_duration, self.movie.pk, mock.ANY),
        ]
        fake_queue.enqueue.assert_has_calls(expected_calls, any_order=True)

        # Finalize job enqueued once
        finalize_calls = [c for c in fake_queue.enqueue.call_args_list if c[0][0] == finalize_conversion]
        self.assertEqual(len(finalize_calls), 1)

    def test_auto_delete_file_on_delete_removes_files(self):
        # Assign additional file fields
        for field in ['thumbnail', 'trailer', 'video_120p', 'video_360p', 'video_720p', 'video_1080p']:
            test_file = SimpleUploadedFile(f'{field}.txt', b'data')
            setattr(self.movie, field, test_file)
        self.movie.save()

        # Collect paths
        paths = []
        for field in ['video_file', 'thumbnail', 'trailer', 'video_120p', 'video_360p', 'video_720p', 'video_1080p']:
            file_field = getattr(self.movie, field)
            paths.append(os.path.join(settings.MEDIA_ROOT, file_field.name))

        # Delete instance
        self.movie.delete()

        # Assert removal
        for path in paths:
            self.assertFalse(os.path.exists(path), f"File {path} should be deleted")
