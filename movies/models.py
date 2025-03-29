from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="movies")
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    conversion_started = models.BooleanField(default=False)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_120p = models.FileField(null=True, blank=True)
    video_360p = models.FileField(null=True, blank=True)
    video_720p = models.FileField(null=True, blank=True)
    video_1080p = models.FileField(null=True, blank=True)
    trailer = models.FileField(upload_to='trailers/', blank=True, null=True)
    def __str__(self):
        return self.title
