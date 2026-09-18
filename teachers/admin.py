from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'designation', 'qualification', 'specialization', 'is_active', 'joining_date')
    list_filter = ('designation', 'qualification', 'is_active', 'is_class_teacher', 'joining_date', 'salary_type')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 
                    'user__email', 'specialization', 'pan_number')
    list_per_page = 50
    filter_horizontal = ('subjects',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'employee_id', 'qualification', 'specialization', 'designation')
        }),
        ('Employment Details', {
            'fields': ('joining_date', 'leaving_date', 'leaving_reason', 'is_active', 
                      'experience_years', 'previous_school')
        }),
        ('Subjects & Classes', {
            'fields': ('subjects', 'is_class_teacher', 'class_teacher_of')
        }),
        ('Banking Information', {
            'fields': ('pan_number', 'bank_account', 'bank_name', 'bank_branch', 'ifsc_code')
        }),
        ('Salary Details', {
            'fields': ('salary', 'salary_type')
        }),
    )
    
    readonly_fields = ('employee_id', 'created_at', 'updated_at')
