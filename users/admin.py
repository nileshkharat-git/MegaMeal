from django.contrib import admin
from users.models import CustomUser, CustomGroup, ExpiringToken,\
                         EmailOtp, LoyaltyPoint, LoyaltyPointLimit,\
                         StoreTime, StoreStatus,StoreStatusLogs

class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    list_filter = ('is_active', )


class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username', 'group', 'is_active')
    list_filter = ('group', 'is_active')

class LoyaltyPointAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'count', 'expires_at')

class LoyaltyPointLimitAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_choice', 'limit')

class StoreTimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'day', 'open_time', 'close_time')

class StoreStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_open')

class StoreStatusLogsAdmin(admin.ModelAdmin):
    list_display = ('id', 'log_message', 'response_status_code', 'log_time')

admin.site.register(CustomUser, UserAdmin)
admin.site.register(CustomGroup, GroupAdmin)
admin.site.register(ExpiringToken)
admin.site.register(EmailOtp)
admin.site.register(LoyaltyPointLimit, LoyaltyPointLimitAdmin)
admin.site.register(LoyaltyPoint, LoyaltyPointAdmin)
admin.site.register(StoreTime, StoreTimeAdmin)
admin.site.register(StoreStatus, StoreStatusAdmin)
admin.site.register(StoreStatusLogs, StoreStatusLogsAdmin)