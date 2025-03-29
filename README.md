🛠️ Bekannter Patch für Django 5.x:
Falls beim Start `timezone.utc` fehlt, ändere
`django_rq/templatetags/django_rq.py`:

from django.utils.timezone import utc  
→ in imports:

from datetime import timezone as dt_timezone
from django.utils import timezone
utc = dt_timezone.utc

→ in Zeile 15:
utc_time = time.replace(tzinfo=utc)