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
                    "progressInSeconds": progress.progressInSeconds
                }
            except MovieProgress.DoesNotExist:
                return None
        return None

class MovieFileSerializer(serializers.ModelSerializer):
    progressInSeconds = serializers.SerializerMethodField()
    class Meta:
        model = Movie
        fields = ['title', 'video_120p', 'video_360p', 'video_720p', 'video_1080p', 'progressInSeconds']
        
    def get_progressInSeconds(self, obj):
        """
        Versuche, das MovieProgress-Objekt für request.user und dieses Movie zu laden.
        Wenn keines existiert, gib 0 zurück.
        """
        user = self.context['request'].user
        try:
            mp = MovieProgress.objects.get(user=user, movie=obj)
            return mp.progressInSeconds or 0
        except MovieProgress.DoesNotExist:
            return 0
        
        
class MovieProgressSerializer(serializers.ModelSerializer):
    movie_id = serializers.IntegerField(write_only=True)
    progressInSeconds = serializers.IntegerField()
    finished = serializers.BooleanField(default=False)
    class Meta:
        model = MovieProgress
        fields = ('movie_id', 'progressInSeconds', 'finished')

    def create(self, validated_data):
        user = self.context['request'].user
        movie_id = validated_data.pop('movie_id')
        obj, _ = MovieProgress.objects.update_or_create(
            user=user,
            movie_id=movie_id,
            defaults=validated_data
        )
        return obj