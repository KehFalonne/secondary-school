from django.db import models
from accounts.models import User

class Teacher(models.Model):
    QUALIFICATION_CHOICES = [
        ('B.Ed', 'Bachelor of Education'),
        ('M.Ed', 'Master of Education'),
        ('B.Sc', 'Bachelor of Science'),
        ('M.Sc', 'Master of Science'),
        ('B.A', 'Bachelor of Arts'),
        ('M.A', 'Master of Arts'),
        ('Ph.D', 'Doctor of Philosophy'),
        ('Other', 'Other'),
    ]
    
    DESIGNATION_CHOICES = [
        ('Principal', 'Principal'),
        ('Vice Principal', 'Vice Principal'),
        ('Head Teacher', 'Head Teacher'),
        ('Senior Teacher', 'Senior Teacher'),
        ('Teacher', 'Teacher'),
        ('Assistant Teacher', 'Assistant Teacher'),
        ('Trainee Teacher', 'Trainee Teacher'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'}, primary_key=True)
    employee_id = models.CharField(max_length=20, unique=True)
    qualification = models.CharField(max_length=50, choices=QUALIFICATION_CHOICES)
    specialization = models.CharField(max_length=100)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES, default='Teacher')
    joining_date = models.DateField()
    subjects = models.ManyToManyField('courses.Subject', related_name='teachers')
    
    # Professional Details
    experience_years = models.IntegerField(default=0)
    previous_school = models.CharField(max_length=200, blank=True)
    pan_number = models.CharField(max_length=10, blank=True, unique=True, null=True)
    bank_account = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    
    # Salary Details
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_type = models.CharField(max_length=20, choices=[
        ('Monthly', 'Monthly'),
        ('Contract', 'Contract'),
        ('Hourly', 'Hourly')
    ], default='Monthly')
    
    # Additional Information
    is_class_teacher = models.BooleanField(default=False)
    class_teacher_of = models.ForeignKey('courses.Class', on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name='class_teacher_info')
    
    # Status
    is_active = models.BooleanField(default=True)
    leaving_date = models.DateField(null=True, blank=True)
    leaving_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['employee_id']
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_teacher = Teacher.objects.order_by('-employee_id').first()
            if last_teacher and last_teacher.employee_id.isdigit():
                last_number = int(last_teacher.employee_id)
                self.employee_id = str(last_number + 1).zfill(6)
            else:
                self.employee_id = '000001'
        super().save(*args, **kwargs)
    
    @property
    def total_experience(self):
        from datetime import date
        if self.joining_date:
            today = date.today()
            years = today.year - self.joining_date.year
            months = today.month - self.joining_date.month
            if months < 0:
                years -= 1
                months += 12
            return f"{years} years, {months} months"
        return "N/A"
    
    @property
    def classes_taught(self):
        from courses.models import Class
        return Class.objects.filter(subjects__in=self.subjects.all()).distinct()
    
    @property
    def total_students(self):
        from students.models import Student
        classes = self.classes_taught
        return Student.objects.filter(class_enrolled__in=classes).count()