from django.contrib import admin
from .models import Attendance, AttendanceReport

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'subject', 'teacher', 'marked_by', 'marked_at')
    list_filter = ('status', 'date', 'subject', 'marked_at')
    search_fields = ('student__user__first_name', 'student__user__last_name', 
                    'student__admission_number', 'subject__name')
    date_hierarchy = 'date'
    list_per_page = 50
    readonly_fields = ('marked_at',)
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'date', 'status')
        }),
        ('Subject & Period', {
            'fields': ('subject', 'period', 'teacher')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'marked_by', 'marked_at')
        }),
    )

@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'year', 'total_days', 'present_days', 
                   'absent_days', 'percentage')
    list_filter = ('month', 'year')
    search_fields = ('student__user__first_name', 'student__user__last_name', 
                    'student__admission_number')
    list_per_page = 50
    
    fieldsets = (
        ('Student & Period', {
            'fields': ('student', 'month', 'year')
        }),
        ('Statistics', {
            'fields': ('total_days', 'present_days', 'absent_days', 'late_days', 
                      'half_days', 'percentage')
        }),
    )
    
    readonly_fields = ('total_days', 'present_days', 'absent_days', 'late_days', 
                      'half_days', 'percentage')