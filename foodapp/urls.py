from django.urls import path
from . import views

urlpatterns = [
    path('menu/', views.menu_list, name='menu-list'),
    path('auth/customer/register/', views.customer_register, name='customer-register'),
    path('auth/customer/verify/', views.customer_verify, name='customer-verify'),
    path('auth/customer/login/', views.customer_login, name='customer-login'),
    path('auth/staff/login/', views.staff_login, name='staff-login'),
    path('auth/send-otp/', views.send_otp, name='send-otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify-otp'),
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/current/', views.get_current_order, name='current-order'),
    path('orders/<str:pk>/', views.OrderUpdateView.as_view(), name='order-update'),
    path('orders/delete-history/', views.delete_order_history, name='delete-order-history'),
    path('tables/', views.list_tables, name='list-tables'),
    path('tables/generate/', views.generate_table, name='generate-table'),
    path('tables/verify/', views.verify_table, name='verify-table'),
    path('tables/verify/<str:table_no>/<str:hash_val>/', views.verify_table, name='verify-table-params'),
    path('tables/<str:table_no>/delete/', views.delete_table, name='delete-table'),
    path('tables/bill/', views.bill_table, name='bill-table'),
    path('payments/create/', views.create_payment_order, name='create-payment-order'),
    path('payments/verify/', views.verify_payment, name='verify-payment'),
    path('send_bill_email/', views.send_bill_email, name='send-bill-email'),
    path('tables/lock/', views.lock_table),
    path('menu/add/', views.add_menu_item),         # POST
    path('menu/<str:pk>/', views.update_menu_item), # PUT
    path('menu/<str:pk>/delete/', views.delete_menu_item)
]