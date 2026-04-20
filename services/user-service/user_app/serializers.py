from rest_framework import serializers
from .models import Profile, Address, Wishlist


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user_id', 'full_name', 'avatar', 'gender', 'date_of_birth', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'user_id', 'recipient_name', 'phone', 'address_type',
            'province', 'district', 'ward', 'street_address', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['id', 'user_id', 'product_id', 'created_at']
        read_only_fields = ['id', 'user_id', 'created_at']
