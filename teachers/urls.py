from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('create/', views.teacher_create, name='teacher_create'),
    path('<str:employee_id>/', views.teacher_detail, name='teacher_detail'),
    path('<str:employee_id>/update/', views.teacher_update, name='teacher_update'),
    path('<str:employee_id>/delete/', views.teacher_delete, name='teacher_delete'),
]
