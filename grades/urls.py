from django.urls import path
from . import views

urlpatterns = [
    # Exam URLs
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:exam_id>/update/', views.exam_update, name='exam_update'),
    path('exams/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),
    path('exams/<int:grade_id>/delete/', views.grade_delete, name='grade_delete'),
    path('exams/<int:exam_id>/grade/', views.grade_exam, name='grade_exam'),
    
    # Grade URLs
    path('grades/', views.grade_list, name='grade_list'),
    path('grades/<int:grade_id>/update/', views.grade_update, name='grade_update'),
]
