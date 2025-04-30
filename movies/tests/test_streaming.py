import os
import tempfile
from django.test import RequestFactory, SimpleTestCase
from movies.utils.streaming import RangeFileResponse

class RangeFileResponseTests(SimpleTestCase):
    def setUp(self):
        # lege eine kleine Testdatei mit bekanntem Inhalt an
        self.content = b'0123456789'
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(self.content)
        tmp.flush()
        tmp.close()
        self.filename = tmp.name
        self.factory = RequestFactory()

    def tearDown(self):
        os.remove(self.filename)

    def test_full_content(self):
        """Wenn kein Range-Header, wird die ganze Datei ausgeliefert."""
        request = self.factory.get('/')
        response = RangeFileResponse(request, self.filename, chunk_size=4, content_type='application/test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        # gesamter Inhalt
        self.assertEqual(b''.join(response.streaming_content), self.content)

    def test_partial_content(self):
        """Mit gültigem Range-Header liefert 206 und korrekten Ausschnitt."""
        # wir fordern bytes 2–5
        request = self.factory.get('/', HTTP_RANGE='bytes=2-5')
        response = RangeFileResponse(request, self.filename, chunk_size=2, content_type='application/test')
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        self.assertEqual(response['Content-Range'], f'bytes 2-5/{len(self.content)}')
        self.assertEqual(response['Content-Length'], '4')
        # liefert Byte 2,3,4,5
        self.assertEqual(b''.join(response.streaming_content), self.content[2:6])

    def test_range_end_omitted(self):
        """Ende leer bedeutet bis zum Dateiende."""
        request = self.factory.get('/', HTTP_RANGE='bytes=7-')
        response = RangeFileResponse(request, self.filename)
        self.assertEqual(response.status_code, 206)
        expected_end = len(self.content) - 1
        self.assertEqual(response['Content-Range'], f'bytes 7-{expected_end}/{len(self.content)}')
        self.assertEqual(b''.join(response.streaming_content), self.content[7:])