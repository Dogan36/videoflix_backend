import os
import re
from django.http import StreamingHttpResponse, FileResponse

class RangeFileResponse(StreamingHttpResponse):
    """
    A simple response class that supports HTTP Range requests for byte ranges.
    """
    def __init__(self, request, filename, chunk_size=8192, content_type='application/octet-stream'):
        file_size = os.path.getsize(filename)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

        if range_match:
            # Parse the requested byte range
            start = int(range_match.group(1))
            end_part = range_match.group(2)
            end = int(end_part) if end_part else file_size - 1
            if end >= file_size:
                end = file_size - 1
            length = end - start + 1

            # Prepare generator that yields only the requested slice
            def stream():
                with open(filename, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            status_code = 206  # Partial Content
            super().__init__(stream(), status=status_code, content_type=content_type)
            # Required headers for Range support
            self['Content-Range']   = f'bytes {start}-{end}/{file_size}'
            self['Accept-Ranges']   = 'bytes'
            self['Content-Length']  = str(length)

        else:
            # No Range header: serve the whole file
            response = FileResponse(open(filename, 'rb'), content_type=content_type)
            super().__init__(response.streaming_content, status=response.status_code, content_type=content_type)
            self['Accept-Ranges'] = 'bytes'

        # Note: StreamingHttpResponse sets .streaming_content automatically
