
from movies.tasks import convert_resolution

from .models import Movie
from movies.utils.wait import wait_until_file_is_ready
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import django_rq
import os
from django.conf import settings
from django.core.files import File
from movies.utils.video import generate_thumbnail, get_video_duration, cut_video_for_trailer



@receiver(post_save, sender=Movie)
def video_post_save(sender, instance, created, **kwargs):
    print("✅ Signal wurde aufgerufen")
    if not instance.video_file:
        print("✅ Signal wurde aufgerufen")
        return

    path = instance.video_file.path

    # Schritt 1: Konvertierung (nur wenn noch nicht gestartet)
    if instance.video_file and not instance.conversion_started:

        instance.conversion_started = True
        instance.save(update_fields=["conversion_started"])

        if wait_until_file_is_ready(path, check_interval=3, required_stable_checks=2, max_wait=1800):
            print(f"✅ Datei gefunden. Starte Konvertierung über RQ.")
            queue = django_rq.get_queue('default')
            movie_id = instance.id

            resolutions = [120, 360, 720, 1080]
            jobs = [
                queue.enqueue(convert_resolution, path, movie_id, res)
                for res in resolutions
            ]

            queue.enqueue("movies.tasks.finalize_conversion", path, movie_id, depends_on=jobs)
        else:
            print(f"❌ Datei konnte nach 1800s nicht stabil geladen werden.")

    # Schritt 2: Thumbnail automatisch erstellen (nur wenn nicht vorhanden)
    if created and not instance.thumbnail:
        try:
            thumb_folder = os.path.join(settings.MEDIA_ROOT, "thumbnails")
            os.makedirs(thumb_folder, exist_ok=True)
            thumb_path = os.path.join(thumb_folder, f"{instance.id}_thumb.webp")

            generate_thumbnail(path, thumb_path)
            with open(thumb_path, 'rb') as f:
                instance.thumbnail.save(f"{instance.id}_thumb.webp", File(f), save=True)

            print("📸 Thumbnail erfolgreich erstellt.")
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen des Thumbnails: {e}")

    # Schritt 3: Dauer setzen (nur wenn noch nicht gesetzt)
    if created and not instance.duration:
        try:
            duration = get_video_duration(path)
            if duration:
                instance.duration = duration
                instance.save(update_fields=["duration"])
        except Exception as e:
            print(f"⚠️ Fehler beim Auslesen der Dauer: {e}")    
    
    if created and not instance.trailer:
        try:
            trailer_folder = os.path.join(settings.MEDIA_ROOT, "trailers")
            os.makedirs(trailer_folder, exist_ok=True)
            trailer_path = os.path.join(trailer_folder, f"{instance.id}_trailer.mp4")

            cut_video_for_trailer(path, trailer_path)

            with open(trailer_path, 'rb') as f:
                instance.trailer.save(f"{instance.id}_trailer.mp4", File(f), save=True)

            print("📸 Trailer erfolgreich erstellt.")
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen des Trailers: {e}")


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



