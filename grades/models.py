import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Exam(models.Model):
    EXAM_TYPES = [
        ('Unit Test', 'Unit Test'),
        ('Midterm', 'Midterm'),
        ('Final', 'Final'),
        ('Quiz', 'Quiz'),
        ('Assignment', 'Assignment'),
        ('Project', 'Project'),
        ('Practical', 'Practical'),
        ('Term', 'Term'),
    ]
    
    TERM_CHOICES = [
        ('1', 'First Term'),
        ('2', 'Second Term'),
        ('3', 'Third Term'),
        ('Annual', 'Annual'),
    ]
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    term = models.CharField(max_length=10, choices=TERM_CHOICES, blank=True)
    subject = models.ForeignKey('courses.Subject', on_delete=models.CASCADE)
    class_name = models.ForeignKey('courses.Class', on_delete=models.CASCADE)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, 
                                   help_text="Weightage in final grade calculation")
    date_conducted = models.DateField()
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    exam_time = models.TimeField(("Time"), auto_now=False, auto_now_add=False, null=True)
    
    class Meta:
        ordering = ['-date_conducted']
        unique_together = ['name', 'class_name', 'subject', 'term']
    
    def __str__(self):
        return f"{self.name} - {self.subject} - {self.class_name}"
    
    @property
    def total_students(self):
        return self.class_name.total_students
    
    @property
    def students_graded(self):
        return self.grades.count()
    
    @property
    def pass_percentage(self):
        passed = self.grades.filter(marks_obtained__gte=self.pass_marks).count()
        total = self.grades.count()
        return (passed / total * 100) if total > 0 else 0

class Grade(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100)'),
        ('A', 'A (80-89)'),
        ('B+', 'B+ (70-79)'),
        ('B', 'B (60-69)'),
        ('C+', 'C+ (50-59)'),
        ('C', 'C (40-49)'),
        ('D', 'D (30-39)'),
        ('F', 'F (Below 30)'),
        ('I', 'Incomplete'),
        ('W', 'Withdrawn'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='grades')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    is_absent = models.BooleanField(default=False)
    evaluated_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True)
    evaluated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'exam']
        ordering = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.exam}: {self.marks_obtained}"
    
    def save(self, *args, **kwargs):
        if not self.is_absent:
            # Calculate grade based on marks
            if self.exam.total_marks > 0:
                percentage = (self.marks_obtained / self.exam.total_marks) * 100
            else:
                percentage = 0
            
            if percentage >= 90:
                self.grade = 'A+'
                self.grade_point = 4.0
            elif percentage >= 80:
                self.grade = 'A'
                self.grade_point = 3.5
            elif percentage >= 70:
                self.grade = 'B+'
                self.grade_point = 3.0
            elif percentage >= 60:
                self.grade = 'B'
                self.grade_point = 2.5
            elif percentage >= 50:
                self.grade = 'C+'
                self.grade_point = 2.0
            elif percentage >= 40:
                self.grade = 'C'
                self.grade_point = 1.5
            elif percentage >= 30:
                self.grade = 'D'
                self.grade_point = 1.0
            else:
                self.grade = 'F'
                self.grade_point = 0.0
        else:
            self.grade = 'AB'
            self.grade_point = 0.0
            self.marks_obtained = 0
        
        super().save(*args, **kwargs)
    
    @property
    def percentage(self):
        if self.exam.total_marks > 0:
            return (self.marks_obtained / self.exam.total_marks) * 100
        return 0
    
    @property
    def is_passed(self):
        return self.marks_obtained >= self.exam.pass_marks

class ReportCard(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='report_cards')
    academic_year = models.CharField(max_length=9)
    term = models.CharField(max_length=10, choices=Exam.TERM_CHOICES)
    class_name = models.ForeignKey('courses.Class', on_delete=models.CASCADE)
    
    # Overall Performance
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_grade = models.CharField(max_length=2, blank=True)
    grade_point_average = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rank = models.IntegerField(null=True, blank=True)
    
    # Attendance Summary
    total_working_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Behavioral Aspects
    remarks = models.TextField(blank=True)
    class_teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    published_date = models.DateField(null=True, blank=True)
    generated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'academic_year', 'term']
        ordering = ['-academic_year', 'term', 'student']
    
    def __str__(self):
        return f"Report Card - {self.student} - {self.academic_year} Term {self.term}"
    
    def calculate_performance(self):
        # Parse academic year dates
        try:
            start_year, end_year = self.academic_year.split('-')
            year_start = datetime.date(int(start_year), 4, 1)
            year_end = datetime.date(int(end_year), 3, 31)
        except (ValueError, IndexError):
            return

        # Get all grades for this term
        grades = Grade.objects.filter(
            student=self.student,
            exam__term=self.term,
            exam__class_name=self.class_name,
            exam__date_conducted__range=[year_start, year_end]
        )
        
        if grades.exists():
            self.total_marks = sum([g.exam.total_marks * g.exam.weightage for g in grades])
            self.obtained_marks = sum([g.marks_obtained * g.exam.weightage for g in grades])
            
            if self.total_marks > 0:
                self.percentage = (self.obtained_marks / self.total_marks) * 100
            
            # Calculate GPA
            total_grade_points = sum([g.grade_point for g in grades])
            self.grade_point_average = total_grade_points / grades.count()
            
            # Determine overall grade
            if self.percentage >= 90:
                self.overall_grade = 'A+'
            elif self.percentage >= 80:
                self.overall_grade = 'A'
            elif self.percentage >= 70:
                self.overall_grade = 'B+'
            elif self.percentage >= 60:
                self.overall_grade = 'B'
            elif self.percentage >= 50:
                self.overall_grade = 'C+'
            elif self.percentage >= 40:
                self.overall_grade = 'C'
            elif self.percentage >= 30:
                self.overall_grade = 'D'
            else:
                self.overall_grade = 'F'
            
            # Calculate attendance
            from attendance.models import Attendance
            
            attendance = Attendance.objects.filter(
                student=self.student,
                date__range=[year_start, year_end]
            )
            
            self.total_working_days = attendance.count()
            self.days_present = attendance.filter(status='Present').count()
            
            if self.total_working_days > 0:
                self.attendance_percentage = (self.days_present / self.total_working_days) * 100
            
            self.save()
    
    def get_subject_wise_marks(self):
        """Return subject-wise marks for the report card"""
        # Parse academic year dates
        try:
            start_year, end_year = self.academic_year.split('-')
            year_start = datetime.date(int(start_year), 4, 1)
            year_end = datetime.date(int(end_year), 3, 31)
        except (ValueError, IndexError):
            return {}

        grades = Grade.objects.filter(
            student=self.student,
            exam__term=self.term,
            exam__class_name=self.class_name,
            exam__date_conducted__range=[year_start, year_end]
        ).select_related('exam', 'exam__subject')
        
        subject_data = {}
        for grade in grades:
            subject = grade.exam.subject
            if subject not in subject_data:
                subject_data[subject] = {
                    'total_marks': 0,
                    'obtained_marks': 0,
                    'grades': [],
                    'grade_points': [],
                }
            
            subject_data[subject]['total_marks'] += grade.exam.total_marks * grade.exam.weightage
            subject_data[subject]['obtained_marks'] += grade.marks_obtained * grade.exam.weightage
            subject_data[subject]['grades'].append(grade.grade)
            subject_data[subject]['grade_points'].append(float(grade.grade_point))
        
        # Calculate averages per subject
        for subject, data in subject_data.items():
            data['percentage'] = (data['obtained_marks'] / data['total_marks'] * 100) if data['total_marks'] > 0 else 0
            data['average_grade_point'] = sum(data['grade_points']) / len(data['grade_points']) if data['grade_points'] else 0
        
        return subject_data