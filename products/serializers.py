from datetime import datetime
from django.utils import timezone
from rest_framework import serializers

from users.models import StoreStatus
from users.serializers import CustomUserSerializer
from products.models import Order, OrderItem, Product, Payment, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')
    
class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    unit_price = serializers.CharField(source='price')
    status = serializers.SerializerMethodField('get_status')

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'unit_price', 'category', 'status')

    def get_category(self, obj):
        return obj.category.all()[0].name

    def get_status(self, obj):
        current_time = timezone.localtime().time()
        try:
            store_status = StoreStatus.objects.get(id=1)
            category = obj.category.all()[0]

            if obj.open_time <= current_time <= obj.close_time:
                if category.open_time <= current_time <= category.close_time:
                    if store_status.is_open:
                        return 'Product is available'
                    else:
                        return 'Store is closed'
                else:
                    if store_status.is_open:
                        return 'Products of this category is not available at this movement'
                    else:
                        return 'Store is closed'
            else:
                if not store_status.is_open:
                    return 'Store is closed'
                
                return f'Product is available only batween {obj.open_time.strftime("%I:%M %p")} to {obj.close_time.strftime("%I:%M %p")}'
              
        except Exception as e:
            return str(e)
    
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    description = serializers.CharField(source='product.description')
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, source='product.price')
    category = serializers.SerializerMethodField(method_name='get_category')

    class Meta:
        model = OrderItem
        fields = ('product_name','description', 'unit_price', 'category', 'quantity', 'price')
    
    def get_category(self, obj):
        return obj.product.category.all()[0].name

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_mode', 'payment_amount')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_details = CustomUserSerializer(source='placed_by')
    payment = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'customer_name', 'created_at', 'subtotal', 'total', \
            'shipping_address','paid', 'customer_details', 'payment','items', 'type', 'status' 
            )
        depth=1

class ProductExcelSerializers(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField('get_image')

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'category', 'image')
    
    def get_category(self, obj):
        return obj.category.all()[0].name

    def get_image(self, obj):
        if obj.image == None or obj.image == "":
            return ""
        else:
            return f'http://127.0.0.1:8000/media/product_images/{obj.image}'

class CategoryExcelSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ('id','name', 'products')

    def get_products(self, obj):
        if len(obj.products.all()) != 0:
            return obj.products.all()[0].name
        else:
            return ""
   

    