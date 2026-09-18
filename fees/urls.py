from django.urls import path
from . import views

urlpatterns = [
    path('', views.fee_dashboard, name='fee_dashboard'),
    path('structure/create/', views.fee_structure_create, name='fee_structure_create'),
    path('type/create/', views.fee_type_create, name='fee_type_create'),
    path('student-fees/', views.student_fee_list, name='student_fee_list'),
    path('payment/record/<int:student_fee_id>/', views.record_payment, name='record_payment'),
    path('receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
]