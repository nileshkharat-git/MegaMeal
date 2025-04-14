from django.http import JsonResponse

from users.models import ExpiringToken

class ExpiringTokenAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        header = request.META.get('HTTP_AUTHORIZATION')
        
        if header and header.startswith('Token '):
            token = header.split(' ')[1]
            try:
                token = ExpiringToken.objects.get(key=token)
            except ExpiringToken.DoesNotExist:
                return JsonResponse({'error':'Invalid token'})
            
            if token.is_expired:
                return JsonResponse({'error':'Token has expired.'})

        response = self.get_response(request)
        return response 