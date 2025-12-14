from rest_framework import serializers
from .models import MenuItem, Order, User, Table
import re


# ---------------- MENU ----------------

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"


# ---------------- ORDERS ----------------

class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'total', 'customer', 'created_at']

    def validate_items(self, items):
        if not isinstance(items, list) or not items:
            raise serializers.ValidationError("Items must be a non-empty list")

        for item in items:
            if 'id' not in item or 'qty' not in item:
                raise serializers.ValidationError(
                    "Each item must contain id and qty"
                )
            if not isinstance(item['qty'], int) or item['qty'] < 1:
                raise serializers.ValidationError("qty must be >= 1")

        return items


# ---------------- USERS ----------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone", "role"]


# ---------------- TABLE ----------------

class TableSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = [
            'id', 'table_no', 'hash', 'active',
            'created_at', 'created_by', 'qr_code_url'
        ]
        read_only_fields = ['hash', 'created_at', 'created_by']

    def get_qr_code_url(self, obj):
        return None


class TableGenerationSerializer(serializers.Serializer):
    range = serializers.CharField(required=True)

    def validate_range(self, value):
        value = value.strip().upper()

        if value.isdigit():
            return {"mode": "count", "count": int(value)}

        if re.match(r"^T\d+$", value):
            return {"mode": "single", "tables": [value]}

        if "-" in value:
            start, end = value.split("-")
            s, e = int(start[1:]), int(end[1:])
            if s > e:
                raise serializers.ValidationError("Invalid range")
            return {
                "mode": "multiple",
                "tables": [f"T{str(i).zfill(2)}" for i in range(s, e + 1)]
            }

        if "," in value:
            return {
                "mode": "multiple",
                "tables": [t.strip() for t in value.split(",")]
            }

        raise serializers.ValidationError("Invalid table format")


# ---------------- AUTH ----------------

class CustomerRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)


class CustomerVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()


class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
