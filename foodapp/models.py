from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('customer', 'Customer'),
        ('chef', 'Chef'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='foodapp_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='foodapp_user_set',
        related_query_name='user',
    )

    def __str__(self):
        return f"{self.role} - {self.phone or self.username}"
import uuid

class MenuItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    category = models.CharField(max_length=50)
    image = models.CharField(max_length=255, blank=True)


    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
        ('customer_paid', 'Customer Paid'),
    ]
    id = models.CharField(max_length=20, primary_key=True)
    items = models.JSONField()  # list of dicts: [{'id': 'm1', 'name': '...', 'price': 8.5, 'qty': 1}, ...]
    total = models.FloatField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    customer = models.JSONField()  # {'phone': '...', 'email': '...'}
    table_no = models.CharField(max_length=10, blank=True, null=True)  # e.g., 'T1'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email}"

class Table(models.Model):
    table_no = models.CharField(max_length=10, unique=True)
    hash = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)

    locked = models.BooleanField(default=False)
    session_id = models.CharField(max_length=64, null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Table {self.table_no}"