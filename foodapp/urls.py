from django.urls import path
from . import views

urlpatterns = [

    # -------- MENU --------
    path('menu/', views.menu_list, name='menu-list'),

    # -------- AUTH --------
    path('auth/customer/register/', views.customer_register),
    path('auth/customer/verify/', views.customer_verify),
    path('auth/customer/login/', views.customer_login),
    path('auth/staff/login/', views.staff_login),
    path('auth/send-otp/', views.send_otp),
    path('auth/verify-otp/', views.customer_verify),

    # -------- ORDERS --------
    path('orders/', views.OrderListCreateView.as_view()),
    path('orders/current/', views.get_current_order),
    path('orders/<str:pk>/', views.OrderUpdateView.as_view()),
    path('orders/delete-history/', views.delete_order_history),

    # -------- TABLES --------
    path('tables/', views.list_tables),
    path('tables/generate/', views.generate_table),
    path('tables/lock/', views.lock_table),          # ✅ REQUIRED
    path('tables/<str:table_no>/delete/', views.delete_table),
    path('tables/bill/', views.bill_table),

    # -------- SCANNER (🔥 MISSING BEFORE) --------
    path('scanner/generate/', views.generate_scanner),   # admin
    path('scanner/verify/<str:scanner_hash>/', views.verify_scanner),

    # -------- PAYMENTS --------
    path('payments/create/', views.create_payment_order),
    path('payments/verify/', views.verify_payment),

    # -------- BILL EMAIL --------
    path('send_bill_email/', views.send_bill_email),
]
