from django.db import models
from accounts.models import User

class Student(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]
    
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('Other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'}, primary_key=True)
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='children', limit_choices_to={'user_type': 'parent'})
    admission_number = models.CharField(max_length=20, unique=True)
    roll_number = models.CharField(max_length=20)
    class_enrolled = models.ForeignKey('courses.Class', on_delete=models.SET_NULL, null=True, 
                                      related_name='students')
    section = models.CharField(max_length=10, blank=True) #Could also allow this particular field in the database
    admission_date = models.DateField()
    
    # Personal Information
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100, blank=True)
    mother_occupation = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    parent_email = models.EmailField(blank=True)
    emergency_contact = models.CharField(max_length=15)
    nationality = models.CharField(max_length=50, default='Cameroonian')
    
    
    # Academic Information
    previous_school = models.CharField(max_length=200, blank=True)
    transfer_certificate = models.FileField(upload_to='transfer_certificates/', blank=True, null=True)
    birth_certificate = models.FileField(upload_to='birth_certificates/', blank=True, null=True)
    
    # Medical Information
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    
    # Additional Information
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='General')
    religion = models.CharField(max_length=50, blank=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, unique=True, null=True)
    
    # Transport
    uses_transport = models.BooleanField(default=False)
    transport_route = models.CharField(max_length=100, blank=True)
    bus_stop = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    leaving_date = models.DateField(null=True, blank=True)
    leaving_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['roll_number']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.admission_number}"
    
    def save(self, *args, **kwargs):
        if not self.admission_number:
            last_student = Student.objects.order_by('-admission_number').first()
            if last_student and last_student.admission_number.isdigit():
                last_number = int(last_student.admission_number)
                self.admission_number = str(last_number + 1).zfill(6)
            else:
                self.admission_number = '000001'
        super().save(*args, **kwargs)
    
    @property
    def current_age(self):
        from datetime import date
        if self.user.date_of_birth:
            today = date.today()
            return today.year - self.user.date_of_birth.year - (
                (today.month, today.day) < (self.user.date_of_birth.month, self.user.date_of_birth.day)
            )
        return None
    
    @property
    def attendance_percentage(self):
        from attendance.models import Attendance
        total = Attendance.objects.filter(student=self).count()
        present = Attendance.objects.filter(student=self, status='Present').count()
        return (present / total * 100) if total > 0 else 0
    
    @property
    def overall_grade(self):
        from grades.models import Grade
        grades = Grade.objects.filter(student=self)
        if grades.exists():
            total_marks = sum([g.marks_obtained for g in grades])
            total_possible = sum([g.exam.total_marks for g in grades])
            percentage = (total_marks / total_possible * 100) if total_possible > 0 else 0
            return self._calculate_grade(percentage)
        return 'N/A'
    
    def _calculate_grade(self, percentage):
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 50:
            return 'D'
        else:
            return 'F'