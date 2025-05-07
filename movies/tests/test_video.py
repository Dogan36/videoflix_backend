import os
import tempfile
import shutil
import subprocess
from django.test import SimpleTestCase, override_settings
from movies.utils.video import (
    convert_video_to_resolution,
    generate_thumbnail,
    get_video_duration,
    cut_video_for_trailer,
)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class VideoUtilsTests(SimpleTestCase):
    def setUp(self):
        fd, self.source_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        with open(self.source_path, "wb") as f:
            f.write(b"DATA")
        import movies.utils.video as video_mod
        self._orig_run = video_mod.subprocess.run
        self.video_mod = video_mod

    def tearDown(self):
        self.video_mod.subprocess.run = self._orig_run
        root = self._get_media_root()
        if os.path.isdir(root):
            shutil.rmtree(root, ignore_errors=True)
        os.remove(self.source_path)

    def _get_media_root(self):
        from django.conf import settings
        return settings.MEDIA_ROOT

    def test_convert_video_to_resolution_creates_file(self):
        def fake_run(cmd, **kwargs):
            target = cmd[-1]
            open(target, "wb").close()
        self.video_mod.subprocess.run = fake_run

        path = convert_video_to_resolution(self.source_path, 360)
        self.assertTrue(path.endswith("_360p.mp4"))
        self.assertTrue(os.path.exists(path))

    def test_generate_thumbnail_creates_file(self):
        def fake_run(cmd, **kwargs):
            target = cmd[-1]
            os.makedirs(os.path.dirname(target), exist_ok=True)
            open(target, "wb").close()
        self.video_mod.subprocess.run = fake_run
        out = os.path.join(self._get_media_root(), "thumb.webp")
        result = generate_thumbnail(self.source_path, out)
        self.assertEqual(result, out)
        self.assertTrue(os.path.exists(out))

    def test_get_video_duration_parses_stdout(self):
        class Dummy:
            stdout = "12.34\n"
        def fake_run(cmd, **kwargs):
            return Dummy()
        self.video_mod.subprocess.run = fake_run

        dur = get_video_duration(self.source_path)
        self.assertAlmostEqual(dur, 12.34, places=2)

    def test_cut_video_for_trailer_creates_file(self):
        def fake_run(cmd, **kwargs):
            target = cmd[-1]
            os.makedirs(os.path.dirname(target), exist_ok=True)
            open(target, "wb").close()
        self.video_mod.subprocess.run = fake_run

        out = os.path.join(self._get_media_root(), "trail.mp4")
        result = cut_video_for_trailer(self.source_path, out, duration=5)
        self.assertEqual(result, out)
        self.assertTrue(os.path.exists(out))