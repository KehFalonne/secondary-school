from django.contrib.auth.models import AbstractUser
from django.db import models
from typing import Optional, Iterable
from django.utils import timezone

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('staff', 'Staff'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    nationality = models.CharField(max_length=50, default='Cameroonian')
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def is_administrator(self):
        return self.user_type == 'admin'
    
    @property
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    @property
    def is_student(self):
        return self.user_type == 'student'
    
    @property
    def is_parent(self):
        return self.user_type == 'parent'
    
class SchoolSettings(models.Model):
    school_name = models.CharField(max_length=200, default="Model Public School")
    school_address = models.TextField(blank=True, default="123 Education Street, Knowledge City")
    school_phone = models.CharField(max_length=20, blank=True, default="+1 234 567 8900")
    school_email = models.EmailField(blank=True, default="info@school.com")
    school_logo = models.ImageField(upload_to='school_branding/', blank=True, null=True)
    
    current_session = models.CharField(max_length=20, default="2023-2024", help_text="e.g. 2023-2024")
    current_term = models.CharField(max_length=20, default="1", choices=[('1', 'First Term'), ('2', 'Second Term'), ('3', 'Third Term')])
    
    def save(self, force_insert: bool = False, force_update: bool = False, using: Optional[str] = None, update_fields: Optional[Iterable[str]] = None) -> None:
        # Ensure only one instance exists
        if not self.pk and SchoolSettings.objects.exists():
            return
        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return "School Configuration"
    
    class Meta:
        verbose_name = "School Settings"
        verbose_name_plural = "School Settings"


class AccessRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=User.USER_TYPE_CHOICES, default='student')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    reason = models.TextField(help_text="Why are you requesting access to the system?")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Approval tracking
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Email notification tracking
    approval_email_sent = models.BooleanField(default=False)
    approval_email_sent_at = models.DateTimeField(null=True, blank=True)
    rejection_email_sent = models.BooleanField(default=False)
    rejection_email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Access Request"
        verbose_name_plural = "Access Requests"
    
    def __str__(self):
        return f"Access Request - {self.first_name} {self.last_name} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
