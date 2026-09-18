from django.urls import path
from . import views

urlpatterns = [
    path('report-cards/', views.report_card_list, name='report_card_list'),
    path('report-cards/student/<str:admission_number>/', views.student_report_cards, name='student_report_cards'),
    path('my-report-cards/', views.student_report_cards, name='my_report_cards'),
    path('report-cards/generate/<int:report_card_id>/', views.generate_report_card, name='generate_report_card'),
    path('report-cards/generate/<int:student_id>/<str:term>/<str:academic_year>/', 
         views.generate_single_report_card, name='generate_single_report_card'),
    path('bulk-report-cards/', views.generate_bulk_report_cards, name='generate_bulk_report_cards'),
]
