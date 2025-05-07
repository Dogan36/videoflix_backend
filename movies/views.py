
from rest_framework import generics, permissions
from movies.throttles import VideoStreamRateThrottle
from .models import Movie, Category
from .serializers import MovieSerializer, MovieProgressSerializer, MovieFileSerializer
from rest_framework.response import Response
from rest_framework import status
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
    Aggregate multiple paginated movie lists for the home screen.
    Supports query parameter:
      - page_size: number of items per section (default: 5)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET request: builds and returns the home screen movie sections.
        """
        page_size = self._get_page_size(request)
        response_data = self._build_home_response(request, page_size)
        return Response(response_data)

    def _get_page_size(self, request):
        try:
            return int(request.query_params.get('page_size', 5))
        except ValueError:
            raise ValidationError({"detail": "Invalid page_size parameter. Must be an integer."})

    def _build_home_response(self, request, page_size):
        """
        Builds the full JSON response for the home page.
        """
        return {
            "newest": self._get_newest_section(request, page_size),
            "recently_watched": self._get_recently_watched_section(request, page_size),
            "finished": self._get_finished_section(request, page_size),
            "categories": self._get_categories_section(request, page_size),
        }

    def _get_newest_section(self, request, page_size):
        queryset = Movie.objects.order_by('-created_at')
        return self._paginate_and_serialize(request, queryset, page_size)

    def _get_recently_watched_section(self, request, page_size):
        user = request.user
        queryset = (
            Movie.objects
                .filter(progress_entries__user=user, progress_entries__finished=False)
                .annotate(
                    last_progress=Max(
                        'progress_entries__updated_at',
                        filter=Q(progress_entries__user=user, progress_entries__finished=False)
                    )
                )
                .order_by('-last_progress')
        )
        return self._paginate_and_serialize(request, queryset, page_size)

    def _get_finished_section(self, request, page_size):
        user = request.user
        queryset = (
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
        return self._paginate_and_serialize(request, queryset, page_size)

    def _get_categories_section(self, request, page_size):
        categories_data = []
        for category in Category.objects.all():
            queryset = Movie.objects.filter(categories=category).order_by('-created_at')
            section_data = self._paginate_and_serialize(request, queryset, page_size)
            categories_data.append({
                "category": category.name,
                "category_id": category.id,
                "results": section_data['results'],
                "next": section_data['next']
            })
        return categories_data

    def _paginate_and_serialize(self, request, queryset, page_size):
        paginator = StandardMoviePagination()
        paginator.page_size = page_size
        page = paginator.paginate_queryset(queryset, request, view=self)
        data = MovieSerializer(page, many=True, context={'request': request}).data
        return {
            "results": data,
            "next": paginator.get_next_link()
        }


class MovieDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve metadata and streaming URLs for a single movie.
    Returns video file fields plus user-specific progress/done flags.
    """
    queryset = Movie.objects.all()
    serializer_class = MovieFileSerializer
    permission_classes = [permissions.IsAuthenticated]


class MovieStreamView(APIView):
    """
    Stream the MP4 file at the requested resolution using HTTP Range support.
    URL kwargs: pk (movie ID), resolution (e.g. '360').
    """
    throttle_classes = [VideoStreamRateThrottle]
   
    def get(self, request, pk, *args, **kwargs):
        movie = get_object_or_404(Movie, pk=pk)
        res = request.query_params.get("resolution", "360")
        field = getattr(movie, f"video_{res}p", None)
        if not field:
            return Response({"detail": "Resolution not available"}, status=404)
        return RangeFileResponse(request, field.path, content_type="video/mp4")

class UpdateProgressAPIView(APIView):
    """
    Endpoint to record the user's playback progress.
    Expects JSON: { movie_id, progressInSeconds, finished }.
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        """
        Validate and save MovieProgress via serializer.
        Returns 200 on success or 400 with errors.
        """
        serializer = MovieProgressSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Progress updated.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LoadMoreMoviesAPIView(ListAPIView):
    """
    Unified 'load more' endpoint for infinite scroll.
    Query params:
      - section: 'newest', 'recently_watched', 'finished', or 'category'
      - category_id: required if section=='category'
      - page, page_size: standard pagination
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardMoviePagination

    def get_queryset(self):
        section = self.request.query_params.get('section')
        if section == 'newest':
            return self._get_newest()
        if section == 'recently_watched':
            return self._get_recently_watched()
        if section == 'finished':
            return self._get_finished()
        if section == 'category':
            return self._get_category()
        return Movie.objects.none()

    def _get_newest(self):
        return Movie.objects.order_by('-created_at')

    def _get_recently_watched(self):
        user = self.request.user
        return (
            Movie.objects
                .filter(progress_entries__user=user)
                .annotate(
                    last_progress=Max(
                        'progress_entries__updated_at',
                        filter=Q(progress_entries__user=user)
                    )
                )
                .order_by('-last_progress')
        )

    def _get_finished(self):
        user = self.request.user
        return (
            Movie.objects
                .filter(progress_entries__user=user, progress_entries__finished=True)
                .annotate(
                    last_progress=Max(
                        'progress_entries__updated_at',
                        filter=Q(
                            progress_entries__user=user,
                            progress_entries__finished=True
                        )
                    )
                )
                .order_by('-last_progress')
        )

    def _get_category(self):
        category_id = self.request.query_params.get('category_id')
        if not category_id:
            return Movie.objects.none()
        return Movie.objects.filter(categories__id=category_id).order_by('-created_at')
