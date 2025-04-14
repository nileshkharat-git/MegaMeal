from django.db import models
from users.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=255)
    open_time = models.TimeField(null=True)
    close_time = models.TimeField(null=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ManyToManyField(Category, related_name='products')
    image = models.ImageField(blank=True, null=True, upload_to='product_images')
    open_time = models.TimeField(null=True)
    close_time = models.TimeField(null=True)

    def __str__(self):
        return self.name
    
        
    
class Order(models.Model):
    PENDING = 'PENDIND'
    PROCESSING = 'PROCESSING'
    COMPLETE = 'COMPLETE'
    READY = 'READY'
    CANCEL = 'CANCEL'

    ORDER_STATUS = {
        PENDING:'Pending',
        PROCESSING:'Processing',
        COMPLETE:'Complete',
        READY:'Ready',
        CANCEL:'Cancel'
    }

    PICKUP = 'PICKUP'
    DELIVERY = 'DELIVERY'
    DINEIN = 'DINE_IN'

    ORDER_TYPE = {
        PICKUP:'Pickup',
        DELIVERY:'Delivery',
        DINEIN:'Dine_in'
    }
    
    customer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField()
    placed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=ORDER_TYPE, default=PICKUP, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default=PENDING, null=True, blank=True)
    
    def __str__(self):
        return self.customer_name
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Payment(models.Model):
    payment_mode = models.CharField(max_length=50)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment')
