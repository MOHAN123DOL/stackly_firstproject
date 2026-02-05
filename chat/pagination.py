from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

class MessagePagination(PageNumberPagination):
    page_size = 20
    