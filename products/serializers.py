from datetime import datetime
from rest_framework import serializers

from users.models import StoreStatus, StoreTime
from users.serializers import CustomUserSerializer
from products.models import Order, OrderItem, Product, Payment, Category

class CategorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'products')
    
    def get_products(self, obj):
        products_data = obj.products.all()
        products = ProductSerializer(products_data, many=True)
        return products.data

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    unit_price = serializers.CharField(source='price')
    status = serializers.SerializerMethodField('get_status')
    image = serializers.ImageField()
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'unit_price', 'category', 'status', 'image')

    def get_category(self, obj):
        return obj.category.all()[0].name

    def get_status(self, obj):
        today = datetime.today().strftime('%A')
        try:
            store_status = StoreStatus.objects.get(id=1)
            store_time = StoreTime.objects.get(day = today.upper())
            category = obj.category.all()[0]
            is_product_available = False
            
            if obj.open_time or obj.close_time:
                is_product_available = True
           
            if store_status.is_open:
                open_time = ''
                close_time = ''
                if is_product_available:
                    if obj.open_time:
                        open_time = obj.open_time
                    elif category.open_time:
                        open_time = category.open_time
                    elif store_time.open_time:
                        open_time = store_time.open_time
                    else:
                        open_time = '-'
                    
                    if obj.close_time:
                        close_time = obj.close_time
                    elif category.close_time:
                        close_time = category.close_time
                    elif store_time.close_time:
                        close_time = store_time.close_time
                    else:
                        close_time = '-'
                
                else:
                    if category.open_time:
                        open_time = category.open_time
                    elif store_time.open_time:
                        open_time = store_time.open_time
                    else:
                        open_time = '-'
                    
                    if category.close_time:
                        close_time = category.close_time
                    elif store_time.close_time:
                        close_time = store_time.close_time
                    else:
                        close_time = '-'
                
                if open_time != '-' and close_time == '-':
                    return f'product is available from {open_time.strftime("%I:%M %p")}'
                
                elif open_time == '-' and close_time != '-':
                    return f'product is available till {close_time.strftime("%I:%M %p")}'
                
                elif open_time == '-' and close_time == '-':
                    return f'product is available'

                return \
                    f'product is available between {open_time.strftime("%I:%M %p")} to {close_time.strftime("%I:%M %p")}'

            else:
                return 'Store is closed'
                
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
   

