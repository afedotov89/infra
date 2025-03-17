"""
API views
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """
    API root endpoint
    """
    return Response({
        'message': 'Welcome to the API',
        'status': 'API is running successfully',
    })
