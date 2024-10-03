from django.contrib import admin

from users.models import User


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    list_display = 'email', 'password', 'auth_type', 'auth_status', 'user_type', 'gender','username'
