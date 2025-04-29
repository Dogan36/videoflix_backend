# Beispiel: StandardMoviePagination (in deiner Pagination-Konfiguration)
from rest_framework.pagination import PageNumberPagination

class StandardMoviePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'