from django.db import models
from django.utils import timezone
from students.models import Student
from courses.models import Class
import uuid

class FeeType(models.Model):
    name = models.CharField(max_length=100)  # e.g., Tuition, Transport, Lab, Exam
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    TERM_CHOICES = [
        ('1', 'First Term'),
        ('2', 'Second Term'),
        ('3', 'Third Term'),
        ('Annual', 'Annual'),
    ]
    
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='fee_structures')
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    academic_year = models.CharField(max_length=20)  # e.g., 2023-2024
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.class_name} - {self.fee_type} ({self.amount})"

class StudentFee(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Paid', 'Paid'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    last_payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.fee_structure}"

    @property
    def balance(self):
        return self.fee_structure.amount - self.amount_paid

class FeePayment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Online', 'Online'),
    ]
    
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)