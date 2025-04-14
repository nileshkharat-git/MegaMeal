from rest_framework import serializers
from .models import CustomUser, CustomGroup, LoyaltyPoint

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'whatsapp_number', 'address', 'group')
    
class CustomGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomGroup
        fields = ('id', 'name', 'role_details', 'is_active')
    
class LoyaltyPointSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source = 'user.username')
    class Meta:
        model = LoyaltyPoint
        fields = ('id', 'count', 'expires_at', 'user')