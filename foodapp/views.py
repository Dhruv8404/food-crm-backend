from curl_cffi import request
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from django.contrib.auth.models import User as DjangoUser  # Use built-in for staff, custom for customers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import MenuItem, Order, User as CustomUser, Table, OTP
from .serializers import MenuItemSerializer, OrderSerializer, UserSerializer, CustomerRegisterSerializer, StaffLoginSerializer, CustomerVerifySerializer, CustomerLoginSerializer, TableSerializer
from .utils import send_otp_email, verify_otp as verify_otp_util
from django.conf import settings
import random
import string
import secrets
import razorpay
import datetime
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def menu_list(request):
    items = MenuItem.objects.all()
    serializer = MenuItemSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_register(request):
    serializer = CustomerRegisterSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data.get('phone')
        email = serializer.validated_data['email']

        # Check if customer exists by email (email is unique)
        customer, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={'role': 'customer', 'phone': phone, 'username': f"{email}_customer", 'is_active': True}
        )
        if not created:
            # Update existing customer
            customer.role = 'customer'
            customer.phone = phone
            customer.is_active = True
            customer.set_unusable_password()
            customer.save()
        else:
            customer.set_unusable_password()
            customer.save()

        # Send OTP via email
        success, message = send_otp_email(email)
        if success:
            return Response({'message': 'OTP sent successfully to your email'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_verify(request):
    print("Request data:", request.data)
    serializer = CustomerVerifySerializer(data=request.data)
    if serializer.is_valid():
        otp = serializer.validated_data['otp']
        email = serializer.validated_data['email']

        success, message = verify_otp_util(email, otp)
        if success:
            try:
                user = CustomUser.objects.get(email=email, role='customer')
                token = RefreshToken.for_user(user).access_token
                return Response({'message': 'Verified successfully', 'role': 'customer', 'token': str(token)}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def staff_login(request):
    serializer = StaffLoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)
        if user:
            user.is_active = True
            role = 'admin' if user.is_superuser else 'chef'
            user.role = role
            user.save()
            token = RefreshToken.for_user(user).access_token
            return Response({'message': 'Login successful', 'role': role, 'token': str(token)}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    success, message = send_otp_email(email)
    if success:
        return Response({'message': 'OTP sent successfully to your email'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')
    if not phone or not otp:
        return Response({'error': 'Phone and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.filter(phone=phone, role='customer').first()
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        email = user.email
    except Exception as e:
        return Response({'error': 'Database error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    success, message = verify_otp_util(email, otp)
    if success:
        # Delete OTP after successful verification
        OTP.objects.filter(email=email).delete()
        token = RefreshToken.for_user(user).access_token
        return Response({'message': 'OTP verified successfully', 'token': str(token), 'role': user.role}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_login(request):
    serializer = CustomerLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email, role='customer')
            user.is_active = True
            user.save()
            token = RefreshToken.for_user(user).access_token
            return Response({'message': 'Login successful', 'role': 'customer', 'token': str(token)}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        user = self.request.user
        if user.role == 'customer':
            return Order.objects.filter(customer__phone=user.phone)
        elif user.role == 'chef':
            return Order.objects.all()  # Chefs see all orders including history
        elif user.role == 'admin':
            return Order.objects.all()
        return Order.objects.none()

    def perform_create(self, serializer):
        request = self.request

        table_no = request.data.get("table_no")
        session_id = request.data.get("session_id")

    # 🔐 TABLE ORDER MUST HAVE VALID SESSION
        if table_no:
            if not session_id:
                raise PermissionDenied("Table session missing")

            try:
                table = Table.objects.get(
                table_no=table_no,
                active=True,
                locked=True,
                session_id=session_id
            )
            except Table.DoesNotExist:
                raise PermissionDenied("Invalid or expired table session")

    # 🚫 Prevent anonymous non-table orders
        if not request.user.is_authenticated and not table_no:
            raise PermissionDenied("Order must be placed via table QR")

    # Customer data
        if request.user.is_authenticated:
            customer_data = {
            "phone": request.user.phone,
            "email": request.user.email,
        }
        else:
            customer_data = {}

    # Calculate total
        items = serializer.validated_data.get("items", [])
        total = sum(item["price"] * item.get("quantity", 1) for item in items)

    # Generate order ID
        while True:
            order_id = "ord_" + "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
            if not Order.objects.filter(id=order_id).exists():
                break

        serializer.save(
        id=order_id,
        customer=customer_data,
        total=total,
        table_no=table_no
    )


class OrderUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'chef':
            return Order.objects.all()  # Chefs see all orders including history
        elif user.role == 'admin':
            return Order.objects.all()
        return Order.objects.none()

    def perform_update(self, serializer):
        print(f"Request data: {self.request.data}")  # Add logging for debugging
        user = self.request.user
        if user.role == 'admin':
            # Admins can update items, table_no, and status
            if 'items' in self.request.data:
                # Recalculate total, ensuring quantity is int
                items = self.request.data['items']
                for item in items:
                    if isinstance(item.get('quantity'), str):
                        try:
                            item['quantity'] = int(item['quantity'])
                        except ValueError:
                            pass  # Let serializer handle validation
                total = sum(item['price'] * item.get('quantity', 1) for item in items)
                serializer.save(total=total)
            else:
                serializer.save()
        elif user.role == 'chef':
            # Chefs can only update status
            if 'status' in self.request.data and len(self.request.data) == 1:
                serializer.save()
            else:
                raise PermissionDenied("Chefs can only update status.")
        else:
            raise PermissionDenied("Unauthorized to update orders.")

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        if user.role != 'admin':
            raise PermissionDenied("Only admins can delete orders.")
        return super().destroy(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_table(request):
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can generate tables'}, status=403)

    data = request.data
    table_nos = []

    # CASE 1: frontend sends tables list
    if 'tables' in data:
        table_nos = data['tables']

    # CASE 2: frontend sends count
    elif 'count' in data:
        count = int(data['count'])
        last = Table.objects.order_by('-id').first()
        start = int(last.table_no[1:]) + 1 if last else 1
        table_nos = [f"T{start + i}" for i in range(count)]

    else:
        return Response({'error': 'Invalid input'}, status=400)

    results = []

    for table_no in table_nos:
        table, _ = Table.objects.get_or_create(
            table_no=table_no,
            defaults={'hash': secrets.token_hex(16), 'active': True}
        )

        scan_url = f"{settings.FRONTEND_BASE_URL}/scan/{table.table_no}/{table.hash}"

        results.append({
            'table_no': table.table_no,
            'hash': table.hash,
            'scan_url': scan_url
        })

    return Response(results, status=201)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_table(request, table_no=None, hash_val=None):
    # Allow both URL params and query params
    if not table_no or not hash_val:
        table_no = request.GET.get('table')
        hash_val = request.GET.get('hash')

    if not table_no or not hash_val:
        return Response(
            {'error': 'Missing table or hash'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        table = Table.objects.get(
            table_no=table_no,
            hash=hash_val,
            active=True
        )

        # ⏱️ session validity (30 minutes)
        SESSION_EXPIRY_SECONDS = 30 * 60

        return Response({
            'valid': True,
            'table_no': table.table_no,
            'session_expires_in': SESSION_EXPIRY_SECONDS,
            'server_time': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    except Table.DoesNotExist:
        return Response(
            {'valid': False, 'error': 'Invalid or inactive table'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_table(request, table_no):
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can delete tables'}, status=status.HTTP_403_FORBIDDEN)
    try:
        table = Table.objects.get(table_no=table_no)
        table.delete()
        return Response({'message': f'Table {table_no} deleted successfully'}, status=status.HTTP_200_OK)
    except Table.DoesNotExist:
        return Response({'error': 'Table not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tables(request):
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can view tables'}, status=403)

    return Response([
        {
            "table_no": t.table_no,
            "hash": t.hash,
            "scan_url": f"{settings.FRONTEND_BASE_URL}/scan/{t.table_no}/{t.hash}"
        }
        for t in Table.objects.filter(active=True)
    ])
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_table(request, table_no):
    if request.user.role != 'admin':
        return Response({'error': 'Only admins'}, status=403)

    new_table_no = request.data.get('new_table_no')
    if not new_table_no:
        return Response({'error': 'new_table_no required'}, status=400)

    try:
        # prevent duplicate table numbers
        if Table.objects.filter(table_no=new_table_no).exists():
            return Response(
                {'error': 'Table number already exists'},
                status=400
            )

        table = Table.objects.get(table_no=table_no)
        table.table_no = new_table_no
        table.save()

        scan_url = f"{settings.FRONTEND_BASE_URL}/scan/{table.table_no}/{table.hash}"

        return Response({
            'table_no': table.table_no,
            'hash': table.hash,
            'scan_url': scan_url
        })

    except Table.DoesNotExist:
        return Response({'error': 'Table not found'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_current_order(request):
    phone = request.GET.get('phone')
    include_paid = request.GET.get('include_paid', 'false').lower() == 'true'
    if not phone:
        return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get orders for this phone number, optionally including paid ones
        orders_query = Order.objects.filter(customer__phone=phone)
        if not include_paid:
            if request.user.is_authenticated and request.user.role in ['chef', 'admin']:
                # Chefs/admins see all orders except those already billed by admin ('paid')
                orders_query = orders_query.exclude(status='paid')
            else:
                # Customers see only unpaid orders (exclude 'paid' and 'customer_paid')
                orders_query = orders_query.exclude(status__in=['paid', 'customer_paid'])
        else:
            # When include_paid=true, show all orders for the phone number
            pass
        orders = orders_query.order_by('-created_at')

        if not orders.exists():
            return Response({'error': 'No orders found'}, status=status.HTTP_200_OK)

        # Return the most recent order for backward compatibility, but include all orders in the response
        most_recent_order = orders.first()
        serializer = OrderSerializer(most_recent_order)

        # Also include all orders in the response
        all_orders_serializer = OrderSerializer(orders, many=True)

        response_data = serializer.data
        response_data['all_orders'] = all_orders_serializer.data

        return Response(response_data)
    except Exception as e:
        return Response({'error': 'Database error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bill_table(request):
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can bill tables'}, status=status.HTTP_403_FORBIDDEN)

    table_no = request.data.get('table_no')
    if not table_no:
        return Response({'error': 'Table number is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get all unpaid orders for this table (exclude both 'paid' and 'customer_paid')
        orders = Order.objects.filter(table_no=table_no).exclude(status__in=['paid', 'customer_paid'])
        if not orders.exists():
            return Response({'error': 'No unpaid orders found for this table'}, status=status.HTTP_404_NOT_FOUND)

        # Mark all orders as paid (admin billing)
        orders.update(status='paid')

        # Calculate total bill amount
        total_bill = sum(order.total for order in orders)

        return Response({
            'message': f'Table {table_no} billed successfully',
            'total_bill': total_bill,
            'orders_count': orders.count()
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Database error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_order(request):
    """Create a Razorpay order for payment"""
    if request.user.role != 'customer':
        return Response({'error': 'Only customers can create payment orders'}, status=status.HTTP_403_FORBIDDEN)

    phone = request.data.get('phone')
    if not phone:
        return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get all unpaid orders for this phone number that are pending for payment
        orders = Order.objects.filter(customer__phone=phone, status='pending')
        if not orders.exists():
            return Response({'error': 'No orders ready for payment. Please wait for your order to be prepared.'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate total amount (convert to paisa for Razorpay)
        total_amount = sum(order.total for order in orders)
        amount_in_paisa = int(total_amount * 100)  # Razorpay expects amount in paisa

        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount_in_paisa,
            'currency': 'INR',
            'payment_capture': '1'  # Auto capture
        })

        return Response({
            'order_id': razorpay_order['id'],
            'amount': amount_in_paisa,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID,
            'orders_count': orders.count(),
            'total_amount': total_amount
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': 'Failed to create payment order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Verify Razorpay payment and update order status"""
    if request.user.role != 'customer':
        return Response({'error': 'Only customers can verify payments'}, status=status.HTTP_403_FORBIDDEN)

    payment_id = request.data.get('payment_id')
    order_id = request.data.get('order_id')
    signature = request.data.get('signature')
    phone = request.data.get('phone')

    if not all([payment_id, order_id, signature, phone]):
        return Response({'error': 'Missing payment verification data'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

        # Verify payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        client.utility.verify_payment_signature(params_dict)

        # Get all unpaid orders for this phone number
        orders = Order.objects.filter(customer__phone=phone).exclude(status__in=['paid', 'customer_paid'])
        if orders.exists():
            # Keep orders as pending (online payment completed, chefs can see and start preparing)
            # No status change needed - orders remain pending for chef visibility

            return Response({
                'message': 'Payment verified successfully',
                'orders_count': orders.count()
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No unpaid orders found'}, status=status.HTTP_404_NOT_FOUND)

    except razorpay.errors.SignatureVerificationError:
        return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Payment verification error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bill_email(request):
    """Send bill details to customer's email"""
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can send bill emails'}, status=status.HTTP_403_FORBIDDEN)

    order_id = request.data.get('order_id')
    if not order_id:
        return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order.objects.get(id=order_id)
        if order.status in ['paid', 'customer_paid']:
            return Response({'error': 'Order is already paid'}, status=status.HTTP_400_BAD_REQUEST)

        customer_email = order.customer.get('email')
        if not customer_email:
            return Response({'error': 'Customer email not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare bill details
        bill_details = f"""
        Dear Customer,

        Here are your bill details for Order #{order.id}:

        Table: {order.table_no or 'N/A'}
        Status: {order.status}
        Total Amount: ₹{order.total:.2f}

        Items:
        """
        for item in order.items:
            bill_details += f"- {item['name']} x {item['qty']} = ₹{(item['price'] * item['qty']):.2f}\n"

        bill_details += f"\nTotal: ₹{order.total:.2f}\n\nThank you for dining with us!"

        # Send email (using existing OTP email function as base)
        from .utils import send_bill_email_util
        success, message = send_bill_email_util(customer_email, bill_details)
        if success:
            return Response({'message': 'Bill sent successfully to customer email'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': 'Failed to send bill email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_order_history(request):
    """Delete all order history (paid and customer_paid orders)"""
    if request.user.role not in ['chef', 'admin']:
        return Response({'error': 'Only chefs and admins can delete order history'}, status=status.HTTP_403_FORBIDDEN)

    try:
        # Deslete all orders with status 'paid' or 'customer_paid'
        deleted_count, _ = Order.objects.filter(status__in=['paid', 'customer_paid']).delete()

        return Response({
            'message': f'Successfully deleted {deleted_count} order history records'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': 'Failed to delete order history'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
