import random
from datetime import datetime
from django.contrib.auth import authenticate
from django.core.mail import EmailMessage
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from users.authentication import ExpiringTokenAuthentication
from users.signals import update_user, delete_user
from users.serializers import CustomUserSerializer, CustomGroupSerializer,\
                              LoyaltyPointSerializer
from users.models import CustomUser, CustomGroup,ExpiringToken, EmailOtp,\
                         LoyaltyPoint, StoreStatus, StoreTime, StoreStatusLogs

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')
    whatsapp_number = request.data.get('whatsapp_number')
    address = request.data.get('address')
    profile_pic = request.data.get('profile_pic')

    role = request.data.get('role') or None

    if password != confirm_password:
        return Response({'error': 'Passwords do not match'}, status=400)
    try:
        if role is not None:            
            group = CustomGroup.objects.get(name=role)
            user = CustomUser.objects.create_user(
                                                  username=username, email=email, password=password,\
                                                  whatsapp_number=whatsapp_number, address=address, group=group,\
                                                 profile_pic=profile_pic)
        
        user = CustomUser.objects.create_user(username=username, email=email, password=password,\
                                              whatsapp_number=whatsapp_number, address=address, \
                                                profile_pic=profile_pic)
        user.save()
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

    return Response({'message': 'User registered successfully'})

@api_view(['POST'])
def create_group(request):
    name = request.data.get('name')
    role_details = request.data.get('role_details')
    try:
        group = CustomGroup.objects.create(name=name, role_details=role_details)
        group.save()
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    return Response({'message': 'Group created successfully'})

class CustomUserViewSet(ModelViewSet):
    queryset = CustomUser.objects.filter(is_deleted=False)
    serializer_class = CustomUserSerializer
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]    

    def create(self, request, *args, **kwargs):
        if request.data.get('password') != request.data.get('confirm_password'):
            return Response({'error': 'Passwords do not match'}, status=400)
        request.data.pop('confirm_password')
        try:
            user_email = request.data['email']

            otp = random.randint(100000, 999999)

            email_otp = EmailOtp.objects.create(email=user_email, otp=otp, data=request.data.copy())
            email_otp.save()
            email = EmailMessage(
                subject='OTP Verification',
                body=f'Your OTP is {otp}',
                to=[user_email]
            )
            email.send(fail_silently=True)


        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
        return Response({'message': 'OTP sent to your email.'})
   
    def update(self, request, *args, **kwargs):
        user = CustomUser.objects.get(id=kwargs['pk'])
        for key in request.data.keys():
            if key == 'password':
                user.set_password(request.data[key])
                user.save()
                update_user.send(CustomUser, instance=user,updated_by=request.user)
                serializer = self.get_serializer(user)
                return Response(serializer.data)
  
            if key == 'group':
                group = CustomGroup.objects.get(name=request.data[key])
                user.group = group 
                user.save()
                return Response({'message':'Group updated successfully'})
        
        update_user.send(CustomUser, instance=user,updated_by=request.user)
        return super().update(request, *args, **kwargs)

    def destroy(self, request,*args, **kwargs):
        instance = self.get_object()
        deleted_by = request.user
        delete_user.send(CustomUser, instance=instance, deleted_by=deleted_by)
        return Response({'message':'User deleted successfully'})
            
@api_view(['POST']) 
def email_otp_verify(request):
    email = request.data.get('email')
    otp = request.data.get('otp')

    try:
        emailOtp = EmailOtp.objects.get(email=email)
        if emailOtp.is_valid(otp) and not emailOtp.is_expired():
            user_data = emailOtp.data
            user = CustomUser.objects.create_user(**user_data)
            emailOtp.delete()

    except Exception as e:
        return Response({'error': str(e)}, status=400)

    return Response({'message': 'Email verified successfully'})

@api_view(['POST'])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        token = ExpiringToken.objects.get(user=user)
        if token and token.is_expired:
            token.delete()
            token = ExpiringToken.objects.create(user=user)
        return Response({'token':token.key})
    else:
        return Response({'error':'Invalid credentials'})
    
class CustomGroupViewSet(ModelViewSet):
    queryset = CustomGroup.objects.filter()
    serializer_class = CustomGroupSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_fields = ('is_active',)
    search_fields = ('name',)
    ordering_fields = ('name',)

    def update(self, request, *args, **kwargs):
        group = CustomGroup.objects.get(id=kwargs['pk'])
        if request.data['active']:
            group.is_active = request.data['active']
            group.save()
            return Response({'message':'Group updated successfully'})
        
        return super().update(request, *args, **kwargs)

@api_view(['POST'])
def get_password_reset_otp(request):
    email = request.data.get('email')
    otp = random.randint(100000, 999999)

    if CustomUser.objects.filter(email=email).exists():
        EmailOtp.objects.create(email=email, otp=otp)
        email = EmailMessage(subject="Password reset OTP", body=f"password reset otp is {otp}", to=[email])
        email.send()
        return Response({'message':'OTP send to your email'})
    else:
        return Response({'error':'User does not exists!'})

@api_view(['POST'])
def verify_password_reset_otp(request):
    email = request.data.get('email')
    user = CustomUser.objects.get(email=email)
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')

    try:
        emailotp = EmailOtp.objects.get(email=email)
                    
        if emailotp.is_valid(otp) and emailotp.is_expired():
            user.set_password(new_password)
            user.save()
            emailotp.delete()
            return Response({'message':'Password has been changed'})
        else:
            return Response({'error':'Otp is not valid!'})
    except Exception as e:
        return Response({'error':str(e)})

@api_view(['GET'])
def search_users(request):
    query_params = request.query_params
    users = CustomUser.objects.all()

    if 'search' in query_params:
        search = request.query_params['search']
        users = users.filter(
            Q(username__icontains = search) | Q(whatsapp_number__icontains = search) | \
            Q(email__icontains = search)
        )

    if 'ordering' in query_params:
        ordering = request.query_params['ordering'] 
        users = users.order_by(ordering)
    
    if 'is_active' in query_params:
        active_status = request.query_params['is_active']
        users = users.filter(is_active = active_status.capitalize())

    if users.exists():
        serialize = CustomUserSerializer(users, many = True)
        return Response(serialize.data, status = 200)    

    return Response({'message':'User not found'})

class LoyaltyPointViewSet(ModelViewSet):
    queryset = LoyaltyPoint.objects.all()
    serializer_class = LoyaltyPointSerializer


@api_view(['GET'])
def check_store_status(request):
    today = datetime.today().strftime('%A')
    current_time = timezone.localtime().time()
    
    try:
        schedule = StoreTime.objects.get(day = today.upper())
        store_status = StoreStatus.objects.get(id=1)
       
        if schedule.open_time <= current_time < schedule.close_time \
            and store_status.update_by_admin == False:
            
            store_status.is_open = True
            store_status.save()

            StoreStatusLogs.objects.create(\
                            log_message='Store status updated---->store is open',\
                            response_status_code='200'
                            )
            return Response({'message':'Store status updated---->store is open'})

        if schedule.close_time <= current_time > schedule.open_time\
              and store_status.update_by_admin == False:
            
            store_status.is_open = False
            store_status.save()
            StoreStatusLogs.objects.create(\
                            log_message='Store status updated---->store is closed',\
                            response_status_code='200'
                            )
            return Response({'message':'Store status updated---->store is closed'})
    except Exception as e:
        StoreStatusLogs.objects.create(log_message=str(e), response_status_code='500')
        return Response({'error':str(e)})