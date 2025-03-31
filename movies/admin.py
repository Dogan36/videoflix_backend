from django.contrib import admin
from .models import Movie, Category

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    readonly_fields = [
        'video_120p',
        'video_360p',
        'video_720p',
        'video_1080p',
        'duration',
        'conversion_started',
        'created_at',
    ]
admin.site.register(Category)
