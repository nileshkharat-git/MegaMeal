import os
import json
import pandas as pd
import requests
import base64

from django.db.models import Sum
from django.conf import settings
from django.http import FileResponse
from django.db.models import Q
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from openpyxl import load_workbook

from users.models import CustomUser
from users.authentication import ExpiringTokenAuthentication
from users.signals import create_loyalty_point
from products.models import Order, OrderItem, Product, Payment,Category
from products.signals import order_confirmed
from products.filters import OrderFilter
from products.paginations import CustomPagination
from products.serializers import OrderSerializer, ProductSerializer,\
                                 ProductExcelSerializers,CategoryExcelSerializer, \
                                 CategorySerializer



class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer    
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    filterset_class = OrderFilter
        
    def create(self, request):
        try:
            order = Order.objects.create(
                customer_name=request.data['customer_name'],\
                placed_by=CustomUser.objects.get(id=request.user.id),\
                shipping_address=request.data['shipping_address'])
            
            subtotal = 0
            total = 0

            for item in request.data['order_items']:
                product = Product.objects.get(id=item['product'])

                if item['quantity']:
                    price = product.price * int(item['quantity'])
                    OrderItem.objects.create(
                        order=order,product=product, quantity=item['quantity'], price = price
                        )
                    subtotal = subtotal + price

                else:
                    OrderItem.objects.create(order=order,product=product, price=product.price)
                    subtotal = subtotal + product.price
            
            order.subtotal = subtotal
            
            if 'discount' in request.data.keys():
                discount = int(request.data['discount'])
                discount = (subtotal* discount/100)
                order.discount = discount
                total = subtotal - discount

            if 'delivery_charge' in request.data.keys():
                delivery_charge = int(request.data['delivery_charge'])
                order.delivery_charge = delivery_charge
                total = total + delivery_charge 

            else:
                total = subtotal
            
            order.total = total

            order.save()            
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)("products", {"type": "order_placed",\
                                                    "message": f"Order placed successfully Order id: {order.id}"})

            order_confirmed.send(
                sender=Order, order=order,\
                 placed_by=request.user, items=order.items.all()
                 )
            
            return Response(
                    {'message':f'Order placed successfully. Order id {order.id}',\
                        'payment_url':'http://localhost:8000/products/payment'}, \
                      status=200
                    )
        except Exception as e:
            order.delete()
            return Response({'error':str(e)}, status=500)


@api_view(['GET'])
def order_report(request):
    orders = Order.objects.all()
    serialize_orders = OrderSerializer(orders, many=True)   
    
    revenue = Order.objects.aggregate(Sum('total'))['total__sum']
    
    top_products = Product.objects.annotate(total_sales=Sum('orderitem__quantity')).order_by('-total_sales')[:5]
    serialize_top_products = ProductSerializer(top_products, many=True) 
    
    return Response({
                     'total_sell':orders.count(),
                     'total_revenue':revenue,\
                     'top_five_product':serialize_top_products.data,\
                     'orders':serialize_orders.data}
                    )

@api_view(['POST'])
def payment(request):
    order_id = request.data.get('order_id')
    payment_amount = request.data.get('payment_amount')
    # currency = request.data.get('currency')

    try:
        order = Order.objects.get(id=order_id)
        if order is not None:
            if not order.paid and (order.total>=(order.paid_amount+payment_amount)):
                # code for razorpay payment link
                # data  ={
                #     'amount':payment_amount,
                #     'currency':currency,
                #     'accept_partial':True,
                #     'customer':{
                #         'name':f'{request.user.first_name} {request.user.last_name}',
                #         'contact':f'{request.user.whatsapp_number}',
                #     },
                # }
                # payent_link = requests.post('https://api.razorpay.com/v1/payment_links/', data=data)

                # if payent_link.status_code != 200:
                #     return Response({'error':'payment faild plaease try again'})
                # short_link = payent_link['short_url']
                # return Response({'payment_link':f'{short_link}'})
                
                payment = Payment.objects.create(payment_amount=payment_amount,order=order)
                order.paid_amount = order.paid_amount + payment.payment_amount

                if order.paid_amount == order.total:   
                    order.paid = True

                order.save()
                create_loyalty_point.send(sender=Payment, order=order)
                return Response({'message':'Payment successfull'})
            
            else:
                return Response({'message':'Bill is already paid'}) 
        else:
            return Response({'message':f'Order not found with order id {order_id}'}) 
        
    except Order.DoesNotExist:
        return Response({'message':'Order not exist'})

    except Exception as e:
        return Response({'message':str(e)})

@api_view(['POST'])
def payment_webhook(request):
    data = json.loads(request.data)
    if data['events'] == 'payment.captured':
        order_id = data['payloads']['payment']['entity']['order_id']
        order = Order.objects.get(id=order_id)
        try:
            payment = Payment.objects.get(order=order)
            order = Order.objects.get(id=payment.order.id)
            order.paid_amount = order.paid_amount + payment.payment_amount
            if order.paid_amount == order.total:    
                order.paid = True
            
            order.save()
            return Response({'message':'Payment successfull. Thank you for payement'})
        except Exception as e:
            return Response({'error':str(e)})
        
@api_view(['GET'])
def product_data_download(request):
    products_data = Product.objects.all()
    products = ProductExcelSerializers(products_data, many=True)
    df_products = pd.DataFrame(products.data)
    
    category_data = Category.objects.all()    
    categories = CategoryExcelSerializer(category_data, many=True)
    df_categories = pd.DataFrame(categories.data)

    with pd.ExcelWriter('products.xlsx', engine='xlsxwriter') as writer:
        df_products.to_excel(writer,sheet_name='products', startrow=1, header=False, index=False)
        df_categories.to_excel(writer,sheet_name='category', startrow=1, header=False, index=False)

        workbook  = writer.book
        product_worksheet = writer.sheets['products']
        category_worksheet = writer.sheets['category']

        header_format = workbook.add_format({'bold': False})

        for col_num, value in enumerate(df_products.columns.values):
            product_worksheet.write(0, col_num, value, header_format)
        
        for col_num, value in enumerate(df_categories.columns.values):
            category_worksheet.write(0, col_num, value, header_format)
        
        
    file_path = os.path.join(settings.BASE_DIR, 'products.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='download.xlsx')


@api_view(['POST'])
def product_data_upload(request):
    if request.FILES:
        try:
            wb = load_workbook(request.FILES['excel_file'])
            ws = wb['products']
            all_rows = list(ws.rows)
            wb.close()

            for row in all_rows[1:]:
                name = row[0].value
                description = row[1].value
                price = float(row[2].value)
                category = row[3].value

                product = Product.objects.create(name = name, description = description, price = price)
 
                category = Category.objects.get(name__iexact=category)
                if category is not None:
                    product.category.add(category)
                    product.save()
        except Exception as e:
            return Response({'error':str(e)})
    return Response({'message':'file upload successfully'})

@api_view(['GET'])
def list_orders_by_status(request):
    data = Order.objects.filter(Q(type = Order.PICKUP) | Q(status = Order.PROCESSING))
    ordres = OrderSerializer(data, many = True)
    return Response(ordres.data, status=200)

@api_view(['POST'])
def change_order_status(request):
    order_id = request.data.get('order_id')
    order_status = request.data.get('order_status')

    try:
        order = Order.objects.get(id=order_id)
        order.status = order_status.upper()
        order.save()
    except Exception as e:
        return Response({'error':str(e)})
    return Response({'message':f'Order staus updated to {order_status}'})
    

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.filter(is_deleted=False)
    serializer_class = CategorySerializer
    
    def create(self, request):
        category_name = request.data['name']
        category = Category.objects.create(name=category_name)

        if 'products' in request.data.keys():
            for product_id in request.data['products']:
                try:
                    product = Product.objects.get(id=product_id)
                    product.category.clear()
                    product.category.add(category)
                    product.save()
                except Product.DoesNotExist:
                    continue
                except Exception as e:
                    return Response({'error':str(e)})
        serialize_category = CategorySerializer(category)
        return Response(serialize_category.data)

    def partial_update(self, request, *args, **kwargs):
        if 'products' in request.data.keys():
            category = Category.objects.get(id=kwargs['pk'])
            for product_id in request.data['products']:
                try:
                    product = Product.objects.get(id=product_id)
                    product.category.clear()
                    product.category.add(category)
                    product.save()
                except Product.DoesNotExist:
                    continue
                except Exception as e:
                    return Response({'error':str(e)})
            
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, **kwargs):
        return Response({'message':'You are not allowed to delete category'})
    
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request, *args, **kwargs):
        if 'category' in self.request.query_params:
            category_name = self.request.query_params.get('category')
            category = Category.objects.get(name__iexact = category_name)
            product_data = Product.objects.filter(category = category.id)
            products = ProductSerializer(product_data, many=True)
            return Response({'id':category.id, 'name':category.name, 'products':products.data})
        
        return super().list(request, *args, **kwargs)

@api_view(['POST'])
def upload_image_from_url(request):
    links = request.data.get('image_url')
    format_type = request.data.get('format_type')
    try:
        if type(links) != list:
            responce = requests.get(links)
            product = Product.objects.get(id=7)
            with open(f'{product.name}_image.{format_type}', 'wb+') as file:
                file.write(responce.content)
                product.image.save(file.name, ContentFile(responce.content), save=True)
                encoded_image = base64.b64encode(responce.content)
                product.base64_image = encoded_image
                product.save()
                return Response({'message':'image uploaded'})
        else:
            products = Product.objects.all()[:len(links)]
            for i in range(len(links)+1):
                product = products[i]
                image = requests.get(links[i])
                with open(f'{product.name}_image.{format_type}', 'wb+') as file:
                    file.write(image.content)
                    product.image.save(file.name, ContentFile(image.content), save=True)
                    encoded_image = base64.b64encode(image.content)
                    product.base64_image = encoded_image
                    product.save()
            return Response({'message':'images uploaded'})
                    
    except Exception as e:
        return Response(str(e))