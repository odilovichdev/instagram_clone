from django.contrib import admin

from users.models import User, UserConfirmation


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'phone_number')


@admin.register(UserConfirmation)
class UserConfirmationModelAdmin(admin.ModelAdmin):
    list_display = 'id', 'user', 'code', 'verify_type', 'expiration_time', 'is_confirmed'