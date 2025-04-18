
from movies.tasks import save_converted_resolution, save_thumbnail, save_trailer, save_video_duration, finalize_conversion
from .models import Movie
from movies.utils.wait import wait_until_file_is_ready
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import django_rq


@receiver(post_save, sender=Movie)
def video_post_save(sender, instance, created, **kwargs):
    print("✅ Signal wurde aufgerufen")
    if not instance.video_file:
        print("✅ Signal wurde aufgerufen, aber keine Videodatei gefunden")
        return

    path = instance.video_file.path
    print(f"DEBUG: Dateipfad der Videodatei: {path}")

    if not instance.conversion_started:
        print("DEBUG: Konvertierung wurde noch nicht gestartet. Setze Flag und starte Jobs.")
        instance.conversion_started = True
        instance.save(update_fields=["conversion_started"])

        if wait_until_file_is_ready(path, check_interval=3, required_stable_checks=2, max_wait=1800):
            print("✅ Datei gefunden. Starte Konvertierung über RQ.")
            queue = django_rq.get_queue('default')
            movie_id = instance.id
         
            # Enqueue der konvertierung tasks für verschiedene Auflösungen
            resolutions = [120, 360, 720, 1080]
            conversion_jobs = [
                queue.enqueue(save_converted_resolution, path, movie_id, res)
                for res in resolutions
            ]
            print("DEBUG: Konvertierungs-Jobs enqueued.")

            # Enqueue Thumbnail-Erstellung
            thumbnail_job = queue.enqueue(save_thumbnail, movie_id, path)
            print("DEBUG: Thumbnail-Job enqueued.")

            # Enqueue Trailer-Erstellung
            trailer_job = queue.enqueue(save_trailer, movie_id, path)
            print("DEBUG: Trailer-Job enqueued.")

            duration_job = queue.enqueue(save_video_duration, movie_id, path)
            print("DEBUG: Duration-Job enqueued.")
            # Alle Jobs in einer Liste zusammenführen
            all_jobs = conversion_jobs + [thumbnail_job, trailer_job, duration_job]
            for job in all_jobs:
                print(f"DEBUG: Job {job.id} hat func_name: '{job.func_name}'")
            # Enqueue finale Aufgabe, die von allen anderen abhängt
            queue.enqueue(finalize_conversion, path, movie_id, depends_on=all_jobs)
            print("DEBUG: Finalize Conversion-Job enqueued (hängt von allen Teiljobs ab).")
        else:
            print("❌ Datei konnte nach 1800s nicht stabil geladen werden.")


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
            print(f'{file_field} was deleted')
            file_field.delete(False)



