import pytz
from django.utils import timezone

def custom_create_token(token_model, user, serializer):
    token = token_model.objects.create(user=user)
    utc_now = timezone.now()
    utc_now = utc_now.replace(tzinfo=pytz.UTC)
    token.created = utc_now
    token.save()
    return serializer(token)