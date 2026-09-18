from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html, mark_safe
from .models import User, SchoolSettings, AccessRequest
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_active') # OR is_staff, date_joined
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 
                                     'address', 'date_of_birth', 'profile_picture',
                                     'gender', 'blood_group', 'nationality')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 
                                   'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type',
                      'first_name', 'last_name', 'is_staff', 'is_active')}
        ),
    )
    
    ordering = ('-date_joined',)


class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user_type', 'status_badge', 'created_at', 'actions_display')
    list_filter = ('status', 'user_type', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('email', 'created_at', 'approved_by', 'approved_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('email', 'user_type', 'first_name', 'last_name', 'phone', 'reason', 'created_at')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    name.short_description = 'Name'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'approved': '#28A745',
            'rejected': '#DC3545',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def actions_display(self, obj):
        if obj.status == 'pending':
            return mark_safe(
                '<a class="button" style="background-color: #28A745;">✓ Approve</a> '
                '<a class="button" style="background-color: #DC3545;">✗ Reject</a>'
            )
        return '—'
    actions_display.short_description = 'Actions'

admin.site.register(User, CustomUserAdmin)
admin.site.register(SchoolSettings)
admin.site.register(AccessRequest, AccessRequestAdmin)
