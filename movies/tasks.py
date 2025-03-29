
import os
from movies.utils.video import convert_video_to_resolution
from movies.models import Movie
from django.conf import settings


def convert_resolution(source_path, movie_id, resolution):
    target_path = convert_video_to_resolution(source_path, resolution)
    relative_path = os.path.relpath(target_path, settings.MEDIA_ROOT)
    
    movie = Movie.objects.get(id=movie_id)

    field_map = {
        120: 'video_120p',
        360: 'video_360p',
        720: 'video_720p',
        1080: 'video_1080p',
    }

    field_name = field_map.get(resolution)
    if field_name:
        setattr(movie, field_name, relative_path)
        movie.save(update_fields=[field_name])
    else:
        print(f"⚠️ Unbekannte Auflösung: {resolution}")

def finalize_conversion(path, movie_id):
    print("✅ Alle Konvertierungen abgeschlossen. Original wird gelöscht.")
    from movies.models import Movie
    movie = Movie.objects.get(id=movie_id)

    # Setze Status "bereit"
    movie.ready = True
    movie.save()
    
    try:
        os.remove(path)
        print(f"🗑️ Original gelöscht: {path}")
    except Exception as e:
        print(f"❗ Fehler beim Löschen: {e}")
