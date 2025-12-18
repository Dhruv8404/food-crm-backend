
from rest_framework import serializers
from .models import MenuItem, Order, User, Table

class MenuItemSerializer(serializers.ModelSerializer):
    image = serializers.CharField(required=False)

    class Meta:
        model = MenuItem
        fields = "__all__"



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['total', 'id', 'customer']

    def validate(self, data):
        # Validate items only if provided
        if 'items' in data:
            items = data.get('items', [])
            if not items:
                raise serializers.ValidationError("Items cannot be empty.")

            for item in items:
                if not isinstance(item, dict):
                    raise serializers.ValidationError("Each item must be an object.")

                if 'id' not in item:
                    raise serializers.ValidationError("Each item must contain menu item id.")

                # Fetch menu item if name/price missing
                if 'price' not in item or 'name' not in item:
                    try:
                        menu = MenuItem.objects.get(id=item['id'])
                        item.setdefault('price', menu.price)
                        item.setdefault('name', menu.name)
                    except MenuItem.DoesNotExist:
                        raise serializers.ValidationError(
                            f"Menu item {item['id']} does not exist."
                        )

                # ✅ USE qty (not quantity)
                qty = item.get('qty', 1)

                if isinstance(qty, str):
                    try:
                        qty = int(qty)
                    except ValueError:
                        raise serializers.ValidationError("qty must be an integer.")

                if not isinstance(qty, int) or qty < 1:
                    raise serializers.ValidationError("qty must be >= 1.")

                item['qty'] = qty  # normalize

        # Validate status
        status = data.get('status')
        if status and status not in dict(Order.STATUS_CHOICES):
            raise serializers.ValidationError("Invalid order status.")

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'


# ---------- AUTH SERIALIZERS ----------

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
