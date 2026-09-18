from django.contrib import admin
from .models import Exam, Grade, ReportCard

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'subject','exam_time', 'class_name', 'term', 
                   'date_conducted', 'total_marks', 'pass_marks', 'created_by')
    list_filter = ('exam_type', 'term', 'date_conducted', 'subject', 'class_name')
    search_fields = ('name', 'subject__name', 'class_name__name')
    date_hierarchy = 'date_conducted'
    list_per_page = 50
    readonly_fields = ('created_at', 'total_students', 'students_graded', 'pass_percentage')
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('name', 'exam_type', 'term', 'date_conducted', 'created_by')
        }),
        ('Subject & Class', {
            'fields': ('subject', 'class_name', 'exam_time')
        }),
        ('Marks & Weightage', {
            'fields': ('total_marks', 'pass_marks', 'weightage')
        }),
        ('Statistics', {
            'fields': ('total_students', 'students_graded', 'pass_percentage'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'marks_obtained', 'grade', 'grade_point')
    list_filter = ('grade', 'is_absent', 'exam')
    search_fields = ('student__first_name', 'student__last_name', 'exam__name')
    list_per_page = 50
    


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'term', 'class_name', 'percentage', 
                   'overall_grade', 'rank', 'is_published', 'published_date')
    list_filter = ('academic_year', 'term', 'is_published', 'published_date', 'class_name')
    search_fields = ('student__user__first_name', 'student__user__last_name', 
                    'student__admission_number')
    list_per_page = 50
    readonly_fields = ('total_marks', 'obtained_marks', 'percentage', 'overall_grade', 
                      'grade_point_average', 'total_working_days', 'days_present', 
                      'attendance_percentage', 'generated_at')
    
    fieldsets = (
        ('Student & Period', {
            'fields': ('student', 'academic_year', 'term', 'class_name')
        }),
        ('Academic Performance', {
            'fields': ('total_marks', 'obtained_marks', 'percentage', 'overall_grade', 
                      'grade_point_average', 'rank')
        }),
        ('Attendance Summary', {
            'fields': ('total_working_days', 'days_present', 'attendance_percentage')
        }),
        ('Remarks', {
            'fields': ('remarks', 'class_teacher_remarks', 'principal_remarks')
        }),
        ('Status', {
            'fields': ('is_published', 'published_date', 'generated_by', 'generated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)
