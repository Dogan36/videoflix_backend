
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
    Returns JSON:
      {
        newest: { results: [...], next: <url> },
        recently_watched: { results: [...], next: <url> },
        finished: { results: [...], next: <url> },
        categories: [ { category, category_id, results: [...], next }, ... ]
      }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET: paginate each section in turn:
          1) newest by created_at,
          2) recently watched by latest progress,
          3) finished by latest progress,
          4) each category by created_at.
        """
        user = request.user
        try:
            page_size = int(request.query_params.get('page_size', 5))
        except ValueError:
            return Response(
                {"detail": "Invalid page_size parameter. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        paginator = StandardMoviePagination()
        paginator.page_size = page_size

        newest_qs = Movie.objects.order_by('-created_at')
        newest_page = paginator.paginate_queryset(newest_qs, request, view=self)
        newest_data = MovieSerializer(newest_page, many=True, context={'request': request}).data
        newest_next = paginator.get_next_link()

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
        """
        Choose the base queryset based on 'section' param:
          - newest: all movies by created_at,
          - recently_watched: filter by this user's progress entries,
          - finished: only those marked finished,
          - category: movies in given category.
        """
        user = self.request.user
        params = self.request.query_params
        section = params.get('section')

        if section == 'newest':
            return Movie.objects.order_by('-created_at')

        if section == 'recently_watched':
            # Annotate each Movie with the latest updated_at from this user's progress entries
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

        if section == 'finished':
            # Only those the user has marked finished, likewise ordered by latest update
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

        if section == 'category':
            category_id = params.get('category_id')
            return Movie.objects.filter(categories__id=category_id).order_by('-created_at')

        # Fallback: leeres QuerySet
        return Movie.objects.none()
    
