from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User,Group
from django.utils import timezone
from rest_framework.authtoken.models import Token

from users.managers import SoftDeleteManager

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey("users.CustomUser",null=True, blank=True, related_query_name='removed by', on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
    
    def delete(self, using=None, deleted_by=None):
        self.is_deleted = True
        self.deleted_by = deleted_by
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None):
        super().delete(using=using)

class UpdateModel(models.Model):
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey("CustomUser",null=True, blank=True, related_name='updated by+', on_delete=models.CASCADE)

    def update(self, using=None, updated_by=None):
        self.updated_at = timezone.now()
        self.updated_by = updated_by
        self.save(using=using)
        
    class Meta:
        abstract = True

class CreateModel(models.Model):
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey("CustomUser",null=True, blank=True, related_name='created by+', on_delete=models.CASCADE)

    def create(self, using=None, created_by=None):
        self.created_at = timezone.now()
        self.created_by = created_by
        self.save(using=using)
        
    class Meta:
        abstract = True

class CustomGroup(Group, SoftDeleteModel, UpdateModel, CreateModel):
    role_details = models.CharField(max_length=100) 
    can_create_user = models.BooleanField(default=False)
    can_delete_user = models.BooleanField(default=False)
    can_view_user = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)   

    
class CustomUser(User, SoftDeleteModel, UpdateModel, CreateModel):
    whatsapp_number = models.CharField(max_length=10, unique=True)
    address = models.CharField(max_length=100)
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True, null=True)

    def __str__(self):
        return self.username
    
            
class ExpiringToken(Token):
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.expires_at = timezone.now() + timedelta(minutes=10)
        return super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return self.expires_at < timezone.now()
    

class EmailOtp(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(blank=True, null=True)
    
    def is_valid(self, otp):
        if self.otp == otp:
            return True
        return False 
    
    def is_expired(self):
        return self.created_at + timedelta(minutes=10) < timezone.now()

class WebPushToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.TextField()

class LoyaltyPointLimit(models.Model):
    TOTAL_TYPE = {
        'SUBTOTAL':'Subtoal',
        'TOTAL':'Total'
    }
    total_choice = models.CharField(max_length=10, choices=TOTAL_TYPE, default=TOTAL_TYPE['SUBTOTAL'])
    limit = models.PositiveIntegerField()

def get_expiry():
    return  timezone.now() + timedelta(days=30)

class LoyaltyPoint(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()
    issued_at = models.DateTimeField(auto_now_add=True) 
    expires_at = models.DateTimeField(default=get_expiry)

    def is_expired(self):
        return timezone.now() > self.expires_at


class StoreTime(models.Model):
    DAY_CHOICE = {
        'MONDAY':'Monday',
        'TUESDAY':'Tuesday',
        'WEDNESDAY':'Wednesday',
        'THURSDAY':'Thursday',
        'FRIDAY':'Friday',
        'SATURDAY':'Saturday',
        'SUNDAY':'Sunday'
    }

    day = models.CharField(max_length=20, choices=DAY_CHOICE)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)

class StoreStatus(models.Model):
    is_open = models.BooleanField(default=False)
    update_by_admin = models.BooleanField(default=False)

class StoreStatusLogs(models.Model):
    log_message = models.CharField(max_length=100)
    response_status_code = models.CharField(max_length=10)
    log_time = models.DateTimeField(auto_now_add=True)