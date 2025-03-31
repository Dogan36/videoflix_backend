from django.urls import path
from . import views


app_name = "movies"

urlpatterns = [
    path('movies/', views.MovieListAPIView.as_view(), name='movie-list'),
    path('movies/home/', views.HomeMoviesAPIView.as_view(), name='movies-home'),
    path('movies/by-category/<int:category_id>/', views.MoviesByCategoryAPIView.as_view(), name='movies-by-category'),
    path('movies/<int:pk>/', views.MovieDetailAPIView.as_view(), name='movie-detail'),
    path('movies/<int:pk>/progress/', views.MovieProgressUpdateAPIView.as_view(), name='movie-progress'),
    path('movies/continue-watching/', views.ContinueWatchingAPIView.as_view(), name='continue-watching'),
    path('movies/watched/', views.WatchedMoviesAPIView.as_view(), name='watched-movies'),
]