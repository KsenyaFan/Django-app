from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile


class CustomUserAdmin(BaseUserAdmin):
    inlines = [
        ProfileInline,
    ]

    def avatar(self, obj):
        return obj.profile.avatar.url if hasattr(obj, "profile") and obj.profile.avatar else "no photo"

    avatar.short_description = "Avatar"

    list_display = ("username", "email", "first_name", "last_name", "avatar")


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
