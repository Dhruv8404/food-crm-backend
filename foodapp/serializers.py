from rest_framework import serializers
from .models import MenuItem, Order, User, Table
from .models import Table, TableQR
import re
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['total', 'id', 'customer']

    def validate(self, data):
        print("Validating order data:", data)  # Add logging for debugging
        # Only validate items if items are being updated (not for partial updates with just status)
        if 'items' in data:
            items = data.get('items', [])
            if not items:
                raise serializers.ValidationError("Items cannot be empty.")

            # Validate each item has required fields
            for item in items:
                if not isinstance(item, dict):
                    raise serializers.ValidationError("Each item must be a dictionary.")
                if 'id' not in item:
                    raise serializers.ValidationError("Each item must have an 'id' field.")
                # Fetch price and name if not provided
                if 'price' not in item or 'name' not in item:
                    try:
                        menu_item = MenuItem.objects.get(id=item['id'])
                        if 'price' not in item:
                            item['price'] = menu_item.price
                        if 'name' not in item:
                            item['name'] = menu_item.name
                    except MenuItem.DoesNotExist:
                        raise serializers.ValidationError(f"Menu item with id {item['id']} does not exist.")
                quantity = item.get('quantity', 1)
                if isinstance(quantity, str):
                    try:
                        quantity = int(quantity)
                        item['quantity'] = quantity
                    except ValueError:
                        raise serializers.ValidationError("Quantity must be a valid integer.")
                if not isinstance(quantity, int) or quantity < 1:
                    raise serializers.ValidationError("Quantity must be a positive integer.")

        status = data.get('status')
        if status and status not in dict(Order.STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status choice.")
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'




class TableSerializer(serializers.ModelSerializer):
    """Serializer for Table model"""
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Table
        fields = ['id', 'table_no', 'hash', 'active', 'created_at', 'created_by', 'qr_code_url']
        read_only_fields = ['hash', 'created_at', 'created_by']
    
    def get_qr_code_url(self, obj):
        """Get the QR code image URL if it exists"""
        try:
            if hasattr(obj, 'qr_code') and obj.qr_code.image:
                return obj.qr_code.image.url
        except:
            pass
        return None
class TableGenerationSerializer(serializers.Serializer):
    """
    This serializer now supports:
      - range: "1"
      - range: "T1"
      - range: "T1-T5"
      - range: "T1,T3,T5"
    """
    range = serializers.CharField(required=True)

    def validate_range(self, value):
        value = value.strip().upper()

        # CASE 1: pure number -> count
        if value.isdigit():
            return {"mode": "count", "count": int(value)}

        # CASE 2: single table "T1"
        if re.match(r"^T\d{1,3}$", value):
            return {"mode": "single", "tables": [value]}

        # CASE 3: range "T1-T5"
        if "-" in value:
            try:
                start, end = value.split("-")
                s = int(start.replace("T", ""))
                e = int(end.replace("T", ""))

                if s > e:
                    raise serializers.ValidationError("Invalid range: start cannot be greater than end")

                tables = [f"T{str(i).zfill(2)}" for i in range(s, e + 1)]
                return {"mode": "multiple", "tables": tables}
            except:
                raise serializers.ValidationError("Invalid range format. Use: T1-T5")

        # CASE 4: list "T1,T3,T5"
        if "," in value:
            raw = value.split(",")
            tables = []

            for t in raw:
                t = t.strip()
                if not re.match(r"^T\d{1,3}$", t):
                    raise serializers.ValidationError(f"Invalid table number: {t}")
                tables.append(t)

            return {"mode": "multiple", "tables": tables}

        raise serializers.ValidationError("Invalid format. Use: '1', 'T1', 'T1-T5', or 'T1,T3,T5'")

# For auth
class CustomerRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=10, required=False)
    email = serializers.EmailField()

class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class CustomerVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    email = serializers.EmailField()

class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
