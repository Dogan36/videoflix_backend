import os
import re
from django.http import FileResponse, HttpResponse
from wsgiref.util import FileWrapper

class RangeFileResponse(HttpResponse):
    """
    Eine sehr einfache FileResponse, die HTTP-Range-Requests bedient.
    """
    def __init__(self, request, filename, chunk_size=8192, content_type='application/octet-stream'):
        file_size = os.path.getsize(filename)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        
        if range_match:
            start = int(range_match.group(1))
            # End kann leer sein => bis Dateiende
            end = range_match.group(2)
            end = int(end) if end else file_size - 1
            if end >= file_size:
                end = file_size - 1
            length = end - start + 1
            
            # Partial Content
            response = HttpResponse(status=206, content_type=content_type)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = str(length)
            
            # FileWrapper mit Slice
            wrapper = FileWrapper(open(filename, 'rb'), chunk_size)
            # skip bis zum Start
            wrapper = (chunk for i, chunk in enumerate(wrapper) if i * chunk_size >= start and i * chunk_size <= end)
            response.streaming_content = wrapper
        else:
            # Kein Range-Header: Ganze Datei
            response = FileResponse(open(filename, 'rb'), content_type=content_type)
            response['Accept-Ranges'] = 'bytes'
        
        super().__init__(
            content=response.streaming_content if hasattr(response, 'streaming_content') else response.content,
            status=response.status_code,
            content_type=content_type
        )
        # alle Range-Header übernehmen
        for h in ('Content-Range', 'Accept-Ranges', 'Content-Length'):
            if h in response:
                self[h] = response[h]