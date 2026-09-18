from django.contrib import admin
from .models import Subject, Class, Timetable

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'credit_hours', 'is_elective', 'created_at')
    list_filter = ('is_elective', 'created_at')
    search_fields = ('name', 'code', 'description')
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'credit_hours', 'is_elective')
        }),
        ('Syllabus', {
            'fields': ('syllabus',)
        }),
    )
    readonly_fields = ('created_at',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'section', 'class_teacher', 'academic_year', 
                   'room_number', 'capacity', 'total_students')
    list_filter = ('academic_year', 'class_teacher')
    search_fields = ('name', 'section', 'room_number')
    filter_horizontal = ('subjects',)
    list_per_page = 50
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'section', 'academic_year', 'class_teacher')
        }),
        ('Details', {
            'fields': ('subjects', 'room_number', 'capacity')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def total_students(self, obj):
        return obj.total_students
    total_students.short_description = 'Students'

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'day', 'period', 'subject', 'teacher', 
                   'start_time', 'end_time', 'room')
    list_filter = ('day', 'class_name', 'subject', 'teacher')
    search_fields = ('class_name__name', 'subject__name', 'teacher__user__first_name')
    list_per_page = 50
    
    fieldsets = (
        ('Class & Schedule', {
            'fields': ('class_name', 'day', 'period')
        }),
        ('Subject & Teacher', {
            'fields': ('subject', 'teacher')
        }),
        ('Timing & Location', {
            'fields': ('start_time', 'end_time', 'room')
        }),
    )
