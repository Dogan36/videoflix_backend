# Beispiel: StandardMoviePagination (in deiner Pagination-Konfiguration)
from rest_framework.pagination import PageNumberPagination

class StandardMoviePagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 50  # oder einen anderen sinnvollen Maximalwert
    page_size = 1  # Standardmäßig nur ein Film, wenn nichts anderes angegeben ist