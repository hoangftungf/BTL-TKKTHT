import uuid
from django.db import models


class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, verbose_name='ID người dùng')
    full_name = models.CharField(max_length=255, blank=True, verbose_name='Họ và tên')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Ảnh đại diện')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name='Giới tính')
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Ngày sinh')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'profiles'
        verbose_name = 'Hồ sơ'
        verbose_name_plural = 'Hồ sơ'

    def __str__(self):
        return self.full_name or str(self.user_id)


class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Nhà riêng'),
        ('office', 'Văn phòng'),
        ('other', 'Khác'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(verbose_name='ID người dùng')
    recipient_name = models.CharField(max_length=255, verbose_name='Tên người nhận')
    phone = models.CharField(max_length=15, verbose_name='Số điện thoại')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home', verbose_name='Loại địa chỉ')
    province = models.CharField(max_length=100, verbose_name='Tỉnh/Thành phố')
    district = models.CharField(max_length=100, verbose_name='Quận/Huyện')
    ward = models.CharField(max_length=100, verbose_name='Phường/Xã')
    street_address = models.CharField(max_length=255, verbose_name='Địa chỉ chi tiết')
    is_default = models.BooleanField(default=False, verbose_name='Mặc định')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'addresses'
        verbose_name = 'Địa chỉ'
        verbose_name_plural = 'Địa chỉ'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.recipient_name} - {self.street_address}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user_id=self.user_id, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(verbose_name='ID người dùng')
    product_id = models.UUIDField(verbose_name='ID sản phẩm')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày thêm')

    class Meta:
        db_table = 'wishlists'
        verbose_name = 'Danh sách yêu thích'
        verbose_name_plural = 'Danh sách yêu thích'
        unique_together = ['user_id', 'product_id']

    def __str__(self):
        return f"{self.user_id} - {self.product_id}"
