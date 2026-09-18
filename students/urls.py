from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('<str:admission_number>/', views.student_detail, name='student_detail'),
    path('<str:admission_number>/update/', views.student_update, name='student_update'),
    path('<str:admission_number>/delete/', views.student_delete, name='student_delete'),
]