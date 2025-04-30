from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="movies")
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, help_text="Optional. Wenn du keinen Thumbnail hochlädst, wird automatisch einer erzeugt.")
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(help_text="Video duration in seconds", editable=False, null=True, blank=True)
    conversion_started = models.BooleanField(default=False)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, help_text="Das Original-Video wird automatisch in verschiedene Auflösungen konvertiert und anschließend gelöscht.")
    video_120p = models.FileField(null=True, blank=True)
    video_360p = models.FileField(null=True, blank=True)
    video_720p = models.FileField(null=True, blank=True)
    video_1080p = models.FileField(null=True, blank=True)
    trailer = models.FileField(upload_to='trailers/', blank=True, null=True, help_text="Optional. Wenn du keinen Trailer hochlädst, wird automatisch einer erzeugt.")
    def __str__(self):
        return self.title

class MovieProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movie_progress")
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE, related_name="progress_entries")
    progressInSeconds = models.PositiveIntegerField(null=True, blank=True)
    finished = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("user", "movie")  # Jeder User kann pro Movie nur einen Eintrag haben

    def __str__(self):
        return f"{self.user.email} – {self.movie.title}"