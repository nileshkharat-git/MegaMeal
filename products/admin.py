from django.contrib import admin

from products.models import Category, Product, Order, OrderItem, Payment
from products.utils import send_email_pdf, send_order_report_email

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ('id','name', 'price', 'open_time', 'close_time')


class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ('id','name', 'open_time', 'close_time')

class OrderAdmin(admin.ModelAdmin):
    model = Order
    list_display = ('id','customer_name', 'total', 'paid_amount', 'paid', 'type', 'status')
    list_filter = ('status', 'type')
    actions = ('send_email_to_admin', 'send_email_to_customers')

    change_form_template = 'admin/custom_change_form.html'

    def response_change(self, request, obj):
        if '_send_email' in request.POST:
            items = obj.items.all()
            recipient_list = [request.user.email]
            
            send_email_pdf(order=obj, items=items, recipient_list=recipient_list, subject='Order report')

        return super().response_change(request, obj)

    @admin.action(description='Send email to admin')
    def send_email_to_admin(self, request, queryset):
        recipient_list = [request.user.email]
        send_order_report_email(orders=queryset,recipient_list=recipient_list)

    @admin.action(description='Send email to customers')  
    def send_email_to_customers(self, request, queryset):
        for order in queryset:
             send_email_pdf(order=order, items=order.items.all(),\
                             recipient_list=[order.placed_by.email], subject='Order invoice')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Payment)