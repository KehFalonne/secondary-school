from django.urls import path
from . import views

urlpatterns = [
    path('take/', views.take_attendance, name='take_attendance'),
    path('list/', views.attendance_list, name='attendance_list'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('update/<int:attendance_id>/', views.update_attendance, name='attendance_update'),
    path('delete/<int:attendance_id>/', views.delete_attendance, name='attendance_delete'),
]