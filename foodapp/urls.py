from django.urls import path
from . import views

urlpatterns = [

    # -------- MENU --------
    path('menu/', views.menu_list, name='menu-list'),

    # -------- AUTH --------
    path('auth/customer/register/', views.customer_register, name='customer-register'),
    path('auth/customer/verify/', views.customer_verify, name='customer-verify'),
    path('auth/customer/login/', views.customer_login, name='customer-login'),
    path('auth/staff/login/', views.staff_login, name='staff-login'),
    path('auth/send-otp/', views.send_otp, name='send-otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify-otp'),

    # -------- ORDERS --------
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/current/', views.get_current_order, name='current-order'),
    path('orders/<str:pk>/', views.OrderUpdateView.as_view(), name='order-update'),
    path('orders/delete-history/', views.delete_order_history, name='delete-order-history'),

    # -------- TABLES / QR --------
    path('tables/', views.list_tables, name='list-tables'),
    path('tables/generate/', views.generate_table, name='generate-table'),
    path('tables/verify/<str:table_no>/<str:hash_val>/', views.verify_table, name='verify-table'),
    path('tables/<str:table_no>/delete/', views.delete_table, name='delete-table'),
    path('tables/bill/', views.bill_table, name='bill-table'),

    # -------- PAYMENTS --------
    path('payments/create/', views.create_payment_order, name='create-payment-order'),
    path('payments/verify/', views.verify_payment, name='verify-payment'),

    # -------- BILL EMAIL --------
    path('send_bill_email/', views.send_bill_email, name='send-bill-email'),
]
