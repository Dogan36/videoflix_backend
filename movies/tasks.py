import os
from movies.utils.video import convert_video_to_resolution, generate_thumbnail, get_video_duration, cut_video_for_trailer
from movies.models import Movie
from django.conf import settings
from django.core.files import File


def save_converted_resolution(source_path, movie_id, resolution):
    target_path = convert_video_to_resolution(source_path, resolution)
    relative_path = os.path.relpath(target_path, settings.MEDIA_ROOT)

    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
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


def save_thumbnail(movie_id, source_path):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        raise

    thumb_folder = os.path.join(settings.MEDIA_ROOT, "thumbnails")
    os.makedirs(thumb_folder, exist_ok=True)
    thumb_path = os.path.join(thumb_folder, f"{movie.title}_thumb.webp")

    generate_thumbnail(source_path, thumb_path)

    relative_thumb_path = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
    setattr(movie, "thumbnail", relative_thumb_path)
    print(f"Thumbnail saved at: {relative_thumb_path}")
    movie.save(update_fields=["thumbnail"])


def save_trailer(movie_id, source_path):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        raise

    trailer_folder = os.path.join(settings.MEDIA_ROOT, "trailers")
    os.makedirs(trailer_folder, exist_ok=True)
    trailer_path = os.path.join(trailer_folder, f"{movie.title}_trailer.mp4")

    cut_video_for_trailer(source_path, trailer_path)

    relative_trailer_path = os.path.relpath(trailer_path, settings.MEDIA_ROOT)
    setattr(movie, "trailer", relative_trailer_path)
    print(f"Trailer saved at: {relative_trailer_path}")
    movie.save(update_fields=["trailer"])



def save_video_duration(movie_id, source_path):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        raise

    duration = get_video_duration(source_path)

    movie.duration = duration
    movie.save(update_fields=["duration"])

def finalize_conversion(path, movie_id):
    from movies.models import Movie
    movie = Movie.objects.get(id=movie_id)
    if movie.video_file:
        movie.video_file.delete(save=False)

    if os.path.exists(path):
        os.remove(path)
    

    movie.video_file = None
    movie.save(update_fields=["video_file"])
        


