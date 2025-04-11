
import os
from movies.utils.video import convert_video_to_resolution, generate_thumbnail, get_video_duration, cut_video_for_trailer
from movies.models import Movie
from django.conf import settings
from django.core.files import File


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

    if not movie.trailer and os.path.exists(path):
        try:
            trailer_folder = os.path.join(settings.MEDIA_ROOT, "trailers")
            os.makedirs(trailer_folder, exist_ok=True)
            trailer_filename = f"{movie_id}_trailer.mp4"
            trailer_path = os.path.join(trailer_folder, trailer_filename)

            # Erstelle den Trailer (z. B. die ersten 10 Sekunden)
            cut_video_for_trailer(path, trailer_path, duration=10)
            with open(trailer_path, "rb") as f:
                movie.trailer.save(trailer_filename, File(f), save=True)
            print(f"🎬 Trailer erfolgreich erstellt: {trailer_filename}")
        except Exception as e:
            print(f"❗ Fehler beim Erstellen des Trailers: {e}")

    # Schritt: Thumbnail erstellen, falls noch nicht vorhanden
    if not movie.thumbnail and os.path.exists(path):
        try:
            thumb_folder = os.path.join(settings.MEDIA_ROOT, "thumbnails")
            os.makedirs(thumb_folder, exist_ok=True)
            thumb_filename = f"{movie_id}_thumb.webp"
            thumb_path = os.path.join(thumb_folder, thumb_filename)

            generate_thumbnail(path, thumb_path)  # Nutzt ffmpeg, um einen Schnappschuss zu erzeugen
            with open(thumb_path, "rb") as f:
                movie.thumbnail.save(thumb_filename, File(f), save=True)
            print(f"📸 Thumbnail erfolgreich erstellt: {thumb_filename}")
        except Exception as e:
            print(f"❗ Fehler beim Erstellen des Thumbnails: {e}")
    
    # Setze Status "bereit"
    movie.ready = True
    movie.save()
    
    try:
        os.remove(path)
        print(f"🗑️ Original gelöscht: {path}")
    except Exception as e:
        print(f"❗ Fehler beim Löschen: {e}")
        


