from django.contrib import admin
from .models import Profile, Address, Wishlist


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'full_name', 'gender', 'date_of_birth', 'created_at')
    search_fields = ('full_name', 'user_id')
    list_filter = ('gender',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'phone', 'province', 'district', 'is_default', 'created_at')
    search_fields = ('recipient_name', 'phone', 'street_address')
    list_filter = ('address_type', 'is_default', 'province')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'product_id', 'created_at')
    search_fields = ('user_id', 'product_id')
