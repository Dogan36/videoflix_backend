from django.urls import path
from . import views


app_name = "movies"

urlpatterns = [
    path('home/', views.HomeMoviesAPIView.as_view(), name='movies-home'),
    path('load-more/', views.LoadMoreMoviesAPIView.as_view(), name='load-more-movies'),
    path("<int:pk>/", views.MovieDetailAPIView.as_view(), name="movie-detail"),
    path("<int:pk>/stream/", views.MovieStreamView.as_view(), name="movie-stream"),
    path('progress/update/', views.UpdateProgressAPIView.as_view(), name='update-progress'),
   
]