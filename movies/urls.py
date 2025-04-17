from django.urls import path
from . import views


app_name = "movies"

urlpatterns = [
    path('home/', views.HomeMoviesAPIView.as_view(), name='movies-home'),
    path('by-category/<int:category_id>/', views.MoviesByCategoryAPIView.as_view(), name='movies-by-category'),
    path("<int:pk>/", views.MovieDetailAPIView.as_view(), name="movie-detail"),
    path("<int:pk>/stream/", views.MovieStreamView.as_view(), name="movie-stream"),
    path('<int:pk>/progress/', views.MovieProgressUpdateAPIView.as_view(), name='movie-progress'),
    path('continue-watching/', views.ContinueWatchingAPIView.as_view(), name='continue-watching'),
    path('watched/', views.WatchedMoviesAPIView.as_view(), name='watched-movies'),
]