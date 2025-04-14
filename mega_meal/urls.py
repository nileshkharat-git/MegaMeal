from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from mega_meal import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index   '),
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
