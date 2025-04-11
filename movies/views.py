from rest_framework import generics, permissions

from movies.throttles import VideoStreamRateThrottle
from .models import Movie, MovieProgress, Category
from .serializers import MovieSerializer, MovieProgressSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import FileResponse
import os





class HomeMoviesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("request.user:", request.user)
        user = request.user

        print(Movie.objects.all())
        newest_movies = Movie.objects.order_by('-created_at')[:5]

        # Zuletzt angesehene Filme (nach aktualisiertem Progress)
        recently_watched_ids = (
            MovieProgress.objects.filter(user=user)
            .values_list('movie_id', flat=True)
            .distinct()
        )
        recently_watched_movies = Movie.objects.filter(id__in=recently_watched_ids)[:5]

        # Bereits gesehene Filme (Progress >= 95%)
        finished_ids = (
            MovieProgress.objects.filter(user=user, finished=True)
            .values_list('movie_id', flat=True)
        )
        finished_movies = Movie.objects.filter(id__in=finished_ids)[:5]

        # Filme pro Kategorie (je 5)
        category_data = []
        categories = Category.objects.all()
        for category in categories:
            movies = Movie.objects.filter(categories=category)[:5]
            serialized = MovieSerializer(movies, many=True, context={'request': request}).data
            category_data.append({
                "category": category.name,
                "movies": serialized
            })

        return Response({
            "newest": MovieSerializer(newest_movies, many=True, context={'request': request}).data,
            "recently_watched": MovieSerializer(recently_watched_movies, many=True, context={'request': request}).data,
            "finished": MovieSerializer(finished_movies, many=True, context={'request': request}).data,
            "categories": category_data
        })

class MovieDetailAPIView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]

class MovieProgressUpdateAPIView(generics.CreateAPIView):
    serializer_class = MovieProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        movie_id = pk
        seconds = request.data.get('progressInSeconds')

        if seconds is None:
            return Response({"detail": "progressInSeconds is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            seconds = int(seconds)
        except ValueError:
            return Response({"detail": "progressInSeconds must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        progress, created = MovieProgress.objects.get_or_create(user=user, movie_id=movie_id)
        progress.progressInSeconds = seconds

        try:
            movie = Movie.objects.get(id=movie_id)
            if seconds and movie.duration:
                percent = (seconds / movie.duration) * 100
                progress.finished = percent >= 95
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

        progress.save()
        serializer = MovieProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class StandardMoviePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'

class MoviesByCategoryAPIView(ListAPIView):
    serializer_class = MovieSerializer
    pagination_class = StandardMoviePagination
    
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return Movie.objects.filter(category_id=category_id).order_by('-created_at')

class ContinueWatchingAPIView(ListAPIView):
    serializer_class = MovieSerializer
    pagination_class = StandardMoviePagination
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        progress_qs = MovieProgress.objects.filter(user=self.request.user, progressInSeconds__gt=2)
        return Movie.objects.filter(id__in=progress_qs.values_list('movie_id', flat=True))


class WatchedMoviesAPIView(ListAPIView):
    serializer_class = MovieSerializer
    pagination_class = StandardMoviePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        progress_qs = MovieProgress.objects.filter(user=self.request.user, progress__gte=95)
        return Movie.objects.filter(id__in=progress_qs.values_list('movie_id', flat=True))
    

class ServeVideoView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [VideoStreamRateThrottle]

    def get(self, request, pk, resolution):
        try:
            movie = Movie.objects.get(id=pk)
        except Movie.DoesNotExist:
            return Response({"detail": "Movie not found."}, status=404)

        video_field = getattr(movie, f"video_{resolution}p", None)

        if not video_field or not video_field.name:
            return Response({"detail": f"{resolution}p version not available."}, status=404)

        video_path = video_field.path
        if not os.path.exists(video_path):
            return Response({"detail": "Video file not found."}, status=404)

        return FileResponse(open(video_path, 'rb'), content_type='video/mp4')