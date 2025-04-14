from django.urls import path
from rest_framework.routers import DefaultRouter
from products import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='orders')
router.register(r'product', views.ProductViewSet, basename='products')
router.register(r'category', views.CategoryViewSet, basename='categories')

urlpatterns = [
    path('order_report/', views.order_report, name='order_report'),
    path('list_orders/', views.list_orders_by_status, name='order_by_status'),
    path('change_order_status/', views.change_order_status, name='change_order_status'),
    path('payment/', views.payment, name='payment'),
    path('payment_webhook/', views.payment_webhook, name='payment_webhook'),
    path('excel_download/', views.product_data_download),
    path('excel_upload/', views.product_data_upload),
] + router.urls