from rest_framework import serializers
from .models import Movie, MovieProgress

class MovieSerializer(serializers.ModelSerializer):
    """
    Serializes basic Movie info along with the authenticated user’s watch progress.
    Fields:
      - id, title, trailer, description, thumbnail, categories: core movie metadata.
      - progress: dynamic field showing how many seconds the user has watched.
    """
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'title', 'trailer', 'description', 'thumbnail', 'categories', 'progress']

    def get_progress(self, obj):
        """
        Return the MovieProgress for the current user and this movie.
        If the user is not authenticated or no record exists, return None.
        """
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
    """
    Provides file URLs and playback state for streaming endpoints.
    Adds:
      - progressInSeconds: last watch position for the current user.
      - finished: flag indicating if the user completed the movie.
    """
    progressInSeconds = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()
    class Meta:
        model = Movie
        fields = ['title', 'video_120p', 'video_360p', 'video_720p', 'video_1080p', 'progressInSeconds', 'finished']
        
    def get_progressInSeconds(self, obj):
        """
        Fetch or default to 0 if no MovieProgress exists for this user.
        """
        user = self.context['request'].user
        try:
            mp = MovieProgress.objects.get(user=user, movie=obj)
            return mp.progressInSeconds or 0
        except MovieProgress.DoesNotExist:
            return 0
    
    def get_finished(self, obj):
        """
        Return whether the current user has marked this movie as finished.
        Defaults to False if no progress record is found.
        """
        user = self.context['request'].user
        try:
            mp = MovieProgress.objects.get(user=user, movie=obj)
            return mp.finished or False
        except MovieProgress.DoesNotExist:
            return False
        
        
class MovieProgressSerializer(serializers.ModelSerializer):
    """
    Allows creating/updating a user's MovieProgress via API.
    Fields:
      - movie_id: identifies which movie to update.
      - progressInSeconds: new playback time.
      - finished: whether the movie is now complete.
    """
    movie_id = serializers.IntegerField(write_only=True)
    progressInSeconds = serializers.IntegerField()
    finished = serializers.BooleanField(default=False)
    class Meta:
        model = MovieProgress
        fields = ('movie_id', 'progressInSeconds', 'finished')

    def create(self, validated_data):
        """
        Update or create the MovieProgress entry for the current user and movie.
        Ensures idempotent behavior on repeated submissions.
        """
        user = self.context['request'].user
        movie_id = validated_data.pop('movie_id')
        obj, _ = MovieProgress.objects.update_or_create(
            user=user,
            movie_id=movie_id,
            defaults=validated_data
        )
        return obj