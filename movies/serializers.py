from rest_framework import serializers
from .models import Movie, MovieProgress

class MovieSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'thumbnail', 'category', 'progress']

    def get_progress(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            try:
                progress = MovieProgress.objects.get(movie=obj, user=user)
                return {
                    "seconds": progress.seconds,
                    "percentage": progress.progress
                }
            except MovieProgress.DoesNotExist:
                return None
        return None


class MovieProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieProgress
        fields = ['id', 'movie', 'progress', 'updated_at']
        read_only_fields = ['id', 'updated_at']