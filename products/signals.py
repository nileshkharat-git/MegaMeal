import threading

from django.dispatch import Signal, receiver
from django.conf import settings
from firebase_admin import messaging

from products.utils import send_email_html, send_email_pdf
from users.models import WebPushToken

order_confirmed = Signal()

@receiver(order_confirmed)
def send_order_email(sender, instance=None, **kwargs):
    order = kwargs['order']
    items = kwargs['items']
    
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [kwargs['placed_by'].email]

    t1 = threading.Thread(target=send_email_html, args=(order, items, from_email, recipient_list))
    t2 = threading.Thread(target=send_email_pdf, args=(order, items, from_email, recipient_list))
    
    t1.start()
    t2.start()
    # token = WebPushToken.objects.get(user=kwargs['placed_by'])

    # message = messaging.Message(
    #                 messaging.Notification(
    #                     title='Notification', 
    #                     body=f'Order is placed.Order ID {order.id}'
    #                     ),
    #                     token=token
    #                 )
    # messaging.send(message)