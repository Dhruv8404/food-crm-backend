import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.timezone import now


# ---------------- USER ----------------

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
        related_name='foodapp_users',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='foodapp_users',
        blank=True
    )

    def __str__(self):
        return f"{self.role} - {self.phone or self.username}"


# ---------------- MENU ----------------

class MenuItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    category = models.CharField(max_length=50)
    image = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# ---------------- TABLE ----------------

class Table(models.Model):
    table_no = models.CharField(max_length=10, unique=True)
    hash = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔐 SESSION LOCKING
    session_id = models.UUIDField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.table_no


# ---------------- ORDERS ----------------

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
        ('customer_paid', 'Customer Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    items = models.JSONField()  
    # [{id, name, price, qty}]

    total = models.FloatField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    table_no = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"


# ---------------- OTP ----------------

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email}"


# ---------------- SCANNER ----------------

class Scanner(models.Model):
    name = models.CharField(max_length=50)
    hash = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
