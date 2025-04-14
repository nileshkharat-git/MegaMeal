from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

class CustomPagination(LimitOffsetPagination):
    limit_query_param = 'page_size'
    def get_paginated_response(self, data):
        return Response({
            'total_pages':self.count,
            'current_page':self.offset,
            'page_limit':self.limit,
            'result':data
        })