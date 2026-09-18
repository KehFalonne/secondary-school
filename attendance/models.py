from django.db import models
from django.apps import apps

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half Day', 'Half Day'),
        ('Excused', 'Excused'),
        ('Sick', 'Sick'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    subject = models.ForeignKey('courses.Subject', on_delete=models.CASCADE, null=True, blank=True)
    period = models.IntegerField(null=True, blank=True)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'student']
        unique_together = ['student', 'date', 'subject', 'period']
        verbose_name_plural = "Attendance Records"
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-fill teacher if subject is provided
        if self.subject and not self.teacher:
            try:
                Timetable = apps.get_model('courses', 'Timetable')
                timetable = Timetable.objects.filter(
                    class_name=self.student.class_enrolled,
                    subject=self.subject
                ).first()
                if timetable:
                    self.teacher = timetable.teacher
            except Exception:
                pass
        super().save(*args, **kwargs)

class AttendanceReport(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    total_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    late_days = models.IntegerField(default=0)
    half_days = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['student', 'month', 'year']
    
    def __str__(self):
        return f"{self.student} - {self.month}/{self.year}"
    
    def calculate_stats(self):
        from django.db.models import Count, Q
        from datetime import date
        
        # Get all attendance for the month
        attendances = Attendance.objects.filter(
            student=self.student,
            date__year=self.year,
            date__month=self.month
        )
        
        self.total_days = attendances.count()
        self.present_days = attendances.filter(status='Present').count()
        self.absent_days = attendances.filter(status='Absent').count()
        self.late_days = attendances.filter(status='Late').count()
        self.half_days = attendances.filter(status='Half Day').count()
        
        # Calculate percentage (Present + Late + Half Day/2)
        effective_present = self.present_days + self.late_days + (self.half_days * 0.5)
        self.percentage = (effective_present / self.total_days * 100) if self.total_days > 0 else 0
        
        self.save()
