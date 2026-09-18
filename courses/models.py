from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    credit_hours = models.IntegerField(default=1)
    is_elective = models.BooleanField(default=False)
    syllabus = models.FileField(upload_to='syllabus/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Class(models.Model):
    name = models.CharField(max_length=50)  # e.g., "10th Grade"
    section = models.CharField(max_length=10)  # e.g., "A", "B"
    class_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='class_teacher_classes')
    subjects = models.ManyToManyField(Subject, related_name='classes')
    room_number = models.CharField(max_length=10, blank=True)
    capacity = models.IntegerField(default=40)
    academic_year = models.CharField(max_length=9, default='2024-2025')  # e.g., 2024-2025
    
    # Timing
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ['name', 'section', 'academic_year']
        ordering = ['name', 'section']
    
    def __str__(self):
        return f"{self.name} - Section {self.section} ({self.academic_year})"
    
    @property
    def total_students(self):
        return self.students.count()
    
    @property
    def available_seats(self):
        return self.capacity - self.total_students
    
    @property
    def student_list(self):
        from students.models import Student
        return Student.objects.filter(class_enrolled=self).order_by('roll_number')

class Timetable(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]
    
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='timetables')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    period = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=10, blank=True)
    
    class Meta:
        ordering = ['day', 'period']
        unique_together = ['class_name', 'day', 'period']
        verbose_name = "Timetable Entry"
        verbose_name_plural = "Timetable"
    
    def __str__(self):
        return f"{self.class_name} - {self.day} Period {self.period}: {self.subject}"
    
    @property
    def duration(self):
        from datetime import datetime
        fmt = '%H:%M:%S'
        start = datetime.strptime(str(self.start_time), fmt)
        end = datetime.strptime(str(self.end_time), fmt)
        duration = end - start
        minutes = duration.seconds // 60
        return f"{minutes} minutes"