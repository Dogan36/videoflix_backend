
import os
from movies.utils.video import convert_video_to_resolution, generate_thumbnail, get_video_duration, cut_video_for_trailer
from movies.models import Movie
from django.conf import settings
from django.core.files import File


def save_converted_resolution(source_path, movie_id, resolution):
    print(f"DEBUG: Starte Konvertierung: {resolution}p für Movie-ID {movie_id}")
    target_path = convert_video_to_resolution(source_path, resolution)
    relative_path = os.path.relpath(target_path, settings.MEDIA_ROOT)
    print(f"DEBUG: Zielpfad für {resolution}p: {relative_path}")

    try:
        movie = Movie.objects.get(id=movie_id)
        print(f"DEBUG: Movie gefunden: {movie}")
    except Movie.DoesNotExist:
        print(f"⚠️ Fehler: Kein Movie mit ID {movie_id} gefunden!")
        raise

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
        print(f"DEBUG: {field_name} für Movie-ID {movie_id} gespeichert.")
    else:
        print(f"⚠️ Unbekannte Auflösung: {resolution}")



def save_thumbnail(movie_id, source_path):
    print(f"DEBUG: Starte Thumbnail-Erstellung für Movie-ID {movie_id}")
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        print(f"⚠️ Fehler: Kein Movie mit ID {movie_id} gefunden beim Thumbnail-Erstellen!")
        raise

    thumb_folder = os.path.join(settings.MEDIA_ROOT, "thumbnails")
    os.makedirs(thumb_folder, exist_ok=True)
    thumb_path = os.path.join(thumb_folder, f"{movie.title}_thumb.webp")
    print(f"DEBUG: Thumbnail-Pfad: {thumb_path}")

    generate_thumbnail(source_path, thumb_path)
    print("DEBUG: Thumbnail generiert.")

    setattr(movie, "thumbnail", thumb_path)
    movie.save(update_fields=["thumbnail"])
    print("📸 Thumbnail erfolgreich gespeichert.")


def save_trailer(movie_id, source_path):
    print(f"DEBUG: Starte Trailer-Erstellung für Movie-ID {movie_id}")
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        print(f"⚠️ Fehler: Kein Movie mit ID {movie_id} gefunden beim Trailer-Erstellen!")
        raise

    trailer_folder = os.path.join(settings.MEDIA_ROOT, "trailers")
    os.makedirs(trailer_folder, exist_ok=True)
    trailer_path = os.path.join(trailer_folder, f"{movie.title}_trailer.mp4")
    print(f"DEBUG: Trailer-Pfad: {trailer_path}")

    cut_video_for_trailer(source_path, trailer_path)
    print("DEBUG: Trailer wurde erstellt.")

    setattr(movie, "trailer", trailer_path)
    # Removed undefined 'debugger' statement
    movie.save(update_fields=["trailer"])
    print("🎬 Trailer erfolgreich gespeichert.")


def save_video_duration(movie_id, source_path):
    print(f"DEBUG: Starte Dauer-Ermittlung für Movie-ID {movie_id}")
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        print(f"⚠️ Fehler: Kein Movie mit ID {movie_id} gefunden beim Dauer-Ermitteln!")
        raise

    duration = get_video_duration(source_path)
    print(f"DEBUG: Dauer ermittelt: {duration} Sekunden")

    movie.duration = duration
    movie.save(update_fields=["duration"])
    print("DEBUG: Dauer erfolgreich gespeichert.")

def finalize_conversion(path, movie_id):
    print("✅ Alle Konvertierungen abgeschlossen. Original wird gelöscht.")
    from movies.models import Movie
    movie = Movie.objects.get(id=movie_id)

    try:
        # Lösche die Datei über das FileField (das sorgt normalerweise
        # auch dafür, dass der entsprechende Storage-Eintrag gelöscht wird).
        if movie.video_file:
            movie.video_file.delete(save=False)
            print("✅ FileField 'video_file' wurde gelöscht.")

        # Lösche die Datei explizit aus dem Dateisystem, falls noch vorhanden.
        if os.path.exists(path):
            os.remove(path)
            print(f"🗑️ Original gelöscht: {path}")
        else:
            print("❗ Originaldatei wurde im Dateisystem nicht gefunden.")
    except Exception as e:
        print(f"❗ Fehler beim Löschen: {e}")

    # Setze das FileField im Model zurück (leeren)
    movie.video_file = None
    movie.save(update_fields=["video_file"])
        


