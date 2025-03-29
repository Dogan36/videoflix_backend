
from movies.tasks import convert_resolution, finalize_conversion
from .models import Movie
from movies.utils.wait import wait_until_file_is_ready
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import django_rq


@receiver(post_save, sender=Movie)
def video_post_save(sender, instance, created, **kwargs):
    if created and instance.video_file and not instance.conversion_started:
        instance.conversion_started = True
        instance.save(update_fields=["conversion_started"])

        path = instance.video_file.path
        
        if wait_until_file_is_ready(path, check_interval=3, required_stable_checks=2, max_wait=1800):
            print(f"✅ Datei gefunden. Starte Konvertierung über RQ.")
            queue = django_rq.get_queue('default')
            movie_id = instance.id

            resolutions = [120, 360, 720, 1080]
            jobs = [
                queue.enqueue(convert_resolution, path, movie_id, res)
                for res in resolutions
            ]

            queue.enqueue(finalize_conversion, path, movie_id, depends_on=jobs)
        else:
            print(f"❌ Datei konnte nach 1800s nicht gefunden werden.")
        
        
             
@receiver(post_delete, sender=Movie)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    file_fields = [
        'video_file',
        'thumbnail',
        'trailer',
        'video_120p',
        'video_360p',
        'video_720p',
        'video_1080p'
    ]
    for field in file_fields:
        file_field = getattr(instance, field, None)
        if file_field:
            file_field.delete(False)
            print(f'{file_field} was deleted')

    