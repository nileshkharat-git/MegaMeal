from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users import views

router = DefaultRouter()
router.register(r'users', views.CustomUserViewSet, basename='users')
router.register(r'groups', views.CustomGroupViewSet, basename='groups')
router.register(r'loyalty-points', views.LoyaltyPointViewSet, basename='loyalty-point')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.register, name='register'),
    path('create-group/', views.create_group, name='create-group'),
    path('login/', views.user_login, name='login'),
    path('verify-otp/', views.email_otp_verify, name='verify-email-otp'),
    path('password-reset-otp/', views.get_password_reset_otp, name='password_reset_otp'),
    path('verify-password-reset-otp/', views.verify_password_reset_otp),
    path('search/', views.search_users, name='search_users'),
    path('check-store-status/', views.check_store_status, name='check-store-status'),
]