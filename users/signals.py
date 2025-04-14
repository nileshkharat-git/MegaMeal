from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

from users.models import ExpiringToken, CustomUser, CustomGroup, LoyaltyPoint,LoyaltyPointLimit
from products.models import Payment

register_user = Signal()
update_user = Signal()
delete_user = Signal()
create_loyalty_point = Signal()

@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        ExpiringToken.objects.create(user=instance)

@receiver(register_user)
def create_timestamp(sender, instance=None, created=False, **kwargs):
    if created:
        created_by = kwargs['created_by']
        created_by = CustomUser.objects.get(id=created_by.id)
        instance.create(using=None, created_by=created_by)

@receiver(update_user)
def update_timestamp(sender, instance=None, **kwargs):
    updated_by = kwargs['updated_by']
    updated_by = CustomUser.objects.get(id=updated_by.id)
    instance.update(using=None, updated_by=updated_by)

@receiver(delete_user)
def delete_timestamp(sender, instance=None, **kwargs):
    deleted_by = kwargs['deleted_by']
    deleted_by = CustomUser.objects.get(id=deleted_by.id)
    instance.delete(using=None, deleted_by=deleted_by)

@receiver(post_save, sender=CustomGroup)
def alter_user_active_status(sender, instance=None, **kwargs):
    CustomUser.objects.filter(group=instance).update(is_active=instance.is_active)


@receiver(create_loyalty_point, sender=Payment)
def loyalty_point_credit(sender, instance=None, **kwargs):
    loyalty_point_limit = LoyaltyPointLimit.objects.get(id=1)
    order = kwargs['order']

    if order.paid == True:
        try:
            loyalty_point = LoyaltyPoint.objects.get(user=order.placed_by)
        except LoyaltyPoint.DoesNotExist:
            loyalty_point = LoyaltyPoint.objects.create(user=order.placed_by, count=0)

        if loyalty_point_limit.total_choice == 'SUBTOTAL' and \
                order.subtotal >= loyalty_point_limit.limit:

            point_count = int(order.subtotal/loyalty_point_limit.limit)
            loyalty_point.count = loyalty_point.count + point_count
            loyalty_point.save()

        elif loyalty_point_limit.total_choice == 'TOTAL' and \
                order.total >= loyalty_point_limit.limit:
            
            point_count = int(order.total/loyalty_point_limit.limit)
            loyalty_point.count = loyalty_point.count + point_count
            loyalty_point.save()                
