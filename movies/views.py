from urllib import request
from rest_framework import generics, permissions

from movies import pagination
from movies.throttles import VideoStreamRateThrottle
from .models import Movie, MovieProgress, Category
from .serializers import MovieSerializer, MovieProgressSerializer, MovieFileSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import FileResponse
import os
from django.shortcuts import get_object_or_404
from movies.utils.streaming import RangeFileResponse
from .pagination import StandardMoviePagination
from django.db.models import Max, Q
class HomeMoviesAPIView(APIView):
    """
    Liefert für jede Sektion paginierte Ergebnisse mit 'results' und 'next'.
    Query-Parameter: page_size (optional, default=5)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # 1) page_size extrahieren
        try:
            page_size = int(request.query_params.get('page_size', 5))
        except ValueError:
            return Response(
                {"detail": "Invalid page_size parameter. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        paginator = StandardMoviePagination()
        paginator.page_size = page_size

        # 2) Newest
        newest_qs = Movie.objects.order_by('-created_at')
        newest_page = paginator.paginate_queryset(newest_qs, request, view=self)
        newest_data = MovieSerializer(newest_page, many=True, context={'request': request}).data
        newest_next = paginator.get_next_link()

        # 3) Recently Watched (nach progress.updated_at sortiert)
        recent_qs = (
            Movie.objects
                 .filter(progress_entries__user=user, progress_entries__finished=False)
                 .annotate(
                     last_progress=Max(
                         'progress_entries__updated_at',
                         filter=Q(progress_entries__user=user, 
                                  progress_entries__finished=False)
                     )
                 )
                 .order_by('-last_progress')
        )
        recent_page = paginator.paginate_queryset(recent_qs, request, view=self)
        recent_data = MovieSerializer(recent_page, many=True, context={'request': request}).data
        recent_next = paginator.get_next_link()

        # 4) Finished (nach progress.updated_at sortiert)
        finished_qs = (
            Movie.objects
                 .filter(progress_entries__user=user, progress_entries__finished=True)
                 .annotate(
                     last_progress=Max(
                         'progress_entries__updated_at',
                         filter=Q(progress_entries__user=user, progress_entries__finished=True)
                     )
                 )
                 .order_by('-last_progress')
        )
        finished_page = paginator.paginate_queryset(finished_qs, request, view=self)
        finished_data = MovieSerializer(finished_page, many=True, context={'request': request}).data
        finished_next = paginator.get_next_link()

        # 5) Categories (je nach category_id paginiert)
        category_data = []
        for category in Category.objects.all():
            cat_qs = Movie.objects.filter(categories=category).order_by('-created_at')
            cat_page = paginator.paginate_queryset(cat_qs, request, view=self)
            cat_data = MovieSerializer(cat_page, many=True, context={'request': request}).data
            cat_next = paginator.get_next_link()
            category_data.append({
                "category": category.name,
                "category_id": category.id,
                "results": cat_data,
                "next": cat_next
            })

        return Response({
            "newest": {"results": newest_data, "next": newest_next},
            "recently_watched": {"results": recent_data, "next": recent_next},
            "finished": {"results": finished_data, "next": finished_next},
            "categories": category_data
        })

class MovieDetailAPIView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieFileSerializer
    permission_classes = [permissions.IsAuthenticated]

class MovieStreamView(APIView):
    def get(self, request, pk, *args, **kwargs):
        movie = get_object_or_404(Movie, pk=pk)
        res = request.query_params.get("resolution", "360")
        field = getattr(movie, f"video_{res}p", None)
        if not field:
            return Response({"detail": "Resolution not available"}, status=404)
        return RangeFileResponse(request, field.path, content_type="video/mp4")

class UpdateProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    print(request)
    def post(self, request):
        serializer = MovieProgressSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Progress updated.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LoadMoreMoviesAPIView(ListAPIView):
    """
    Unified endpoint to load more movies for different sections:
    - section=newest
    - section=recently_watched
    - section=finished
    - section=category (requires category_id)
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardMoviePagination

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params
        section = params.get('section')

        if section == 'newest':
            return Movie.objects.order_by('-created_at')

        if section == 'recently_watched':
            ids = (
                MovieProgress.objects
                    .filter(user=user)
                    .values_list('movie_id', flat=True)
                    .distinct()
            )
            return Movie.objects.filter(id__in=ids).order_by('-updated_at')

        if section == 'finished':
            ids = (
                MovieProgress.objects
                    .filter(user=user, finished=True)
                    .values_list('movie_id', flat=True)
            )
            return Movie.objects.filter(id__in=ids).order_by('-updated_at')

        if section == 'category':
            category_id = params.get('category_id')
            return Movie.objects.filter(categories__id=category_id).order_by('-created_at')

        # Fallback: leeres QuerySet
        return Movie.objects.none()
    

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