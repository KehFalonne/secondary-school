from django.urls import path
from . import views

urlpatterns = [
    # Class URLs
    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    path('classes/<int:class_id>/', views.class_detail, name='class_detail'),
    path('classes/<int:class_id>/update/', views.class_update, name='class_update'),
    
    # Subject URLs
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:subject_id>/update/', views.subject_update, name='subject_update'),
    path('subjects/<int:subject_id>/delete/', views.subject_delete, name='subject_delete'),
    
    # Timetable URLs
    path('timetable/', views.timetable, name='timetable'),
    path('timetable/<int:class_id>/', views.timetable, name='timetable_class'),
    path('timetable/manage/', views.timetable_form, name='timetable_form'),
    path('timetable/manage/<int:class_id>/', views.timetable_form, name='timetable_form_class'),
]
