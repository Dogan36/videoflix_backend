from rest_framework import serializers
from .models import Movie, MovieProgress

class MovieSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'title', 'trailer', 'description', 'thumbnail', 'categories', 'progress']

    def get_progress(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            try:
                progress = MovieProgress.objects.get(movie=obj, user=user)
                return {
                    "progressInSeconds": progress.progressInseconds
                }
            except MovieProgress.DoesNotExist:
                return None
        return None

class MovieFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Movie
        fields = ['title', 'video_120p', 'video_360p', 'video_720p', 'video_1080p']

class MovieProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieProgress
        fields = ['id', 'movie', 'progress']
        read_only_fields = ['id']