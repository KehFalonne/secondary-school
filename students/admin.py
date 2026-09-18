from django.contrib import admin
from .models import Student
from import_export.admin import ImportExportModelAdmin

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    list_display = ('admission_number', 'user', 'class_enrolled', 'roll_number', 'is_active', 'admission_date')
    list_filter = ('class_enrolled', 'is_active', 'admission_date', 'user__gender', 'category')
    search_fields = ('admission_number', 'roll_number', 'user__first_name', 'user__last_name', 
                    'user__email', 'father_name', 'mother_name')
    list_per_page = 50
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'admission_number', 'roll_number', 'class_enrolled') # Can add the 'section' field if wanted
        }),
        ('Parent Information', {
            'fields': ('father_name', 'mother_name', 'father_occupation', 'mother_occupation',
                      'parent_phone', 'parent_email', 'emergency_contact', 'parent')
        }),
        ('Academic Information', {
            'fields': ('admission_date', 'previous_school', 'category', 'religion')
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'medical_conditions', 'allergies')
        }),
        ('Transport', {
            'fields': ('uses_transport', 'transport_route', 'bus_stop')
        }),
        ('Documents', {
            'fields': ('transfer_certificate', 'birth_certificate', 'aadhaar_number')
        }),
        ('Status', {
            'fields': ('is_active', 'leaving_date', 'leaving_reason')
        }),
    )
    
    readonly_fields = ('admission_number', 'created_at', 'updated_at')