import os
import re
from django.http import StreamingHttpResponse, FileResponse

class RangeFileResponse(StreamingHttpResponse):
    """
    A response class that supports HTTP Range requests for byte ranges.
    Useful for streaming video/audio files efficiently.
    """

    def __init__(self, request, filename, chunk_size=8192, content_type='application/octet-stream'):
        self.file_size = os.path.getsize(filename)
        self.filename = filename
        self.chunk_size = chunk_size
        self.content_type = content_type

        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

        if range_match:
            self._handle_partial_content(range_match)
        else:
            self._handle_full_content()

    def _parse_range(self, match):
        start = int(match.group(1))
        end_part = match.group(2)
        end = int(end_part) if end_part else self.file_size - 1
        end = min(end, self.file_size - 1)
        return start, end

    def _file_stream(self, start, end):
        def generator():
            with open(self.filename, 'rb') as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(self.chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        return generator()

    def _set_partial_headers(self, start, end):
        self['Content-Range'] = f'bytes {start}-{end}/{self.file_size}'
        self['Accept-Ranges'] = 'bytes'
        self['Content-Length'] = str(end - start + 1)

    def _handle_partial_content(self, range_match):
        start, end = self._parse_range(range_match)
        stream = self._file_stream(start, end)
        status_code = 206  # Partial Content
        super(RangeFileResponse, self).__init__(stream, status=status_code, content_type=self.content_type)
        self._set_partial_headers(start, end)

    def _handle_full_content(self):
        response = FileResponse(open(self.filename, 'rb'), content_type=self.content_type)
        super(RangeFileResponse, self).__init__(
            response.streaming_content,
            status=response.status_code,
            content_type=self.content_type
        )
        self['Accept-Ranges'] = 'bytes'

