from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from .models import FeeStructure, StudentFee, FeePayment, FeeType
from .forms import FeeStructureForm, FeePaymentForm, FeeTypeForm
from students.models import Student
from courses.models import Class
import datetime

def is_admin(user):
    return user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def fee_dashboard(request):
    # Statistics
    total_collected = FeePayment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expected = StudentFee.objects.aggregate(total=Sum('fee_structure__amount'))['total'] or 0
    pending_amount = total_expected - total_collected
    
    recent_payments = FeePayment.objects.select_related('student_fee__student__user').order_by('-created_at')[:10]
    
    # Fee Structures
    fee_structures = FeeStructure.objects.select_related('class_name', 'fee_type').all().order_by('-created_at')
    
    context = {
        'total_collected': total_collected,
        'total_expected': total_expected,
        'pending_amount': pending_amount,
        'recent_payments': recent_payments,
        'fee_structures': fee_structures,
        'fee_type_form': FeeTypeForm(),
    }
    return render(request, 'fees/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def fee_structure_create(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            structure = form.save()
            
            # Auto-assign to existing students in the class
            students = Student.objects.filter(class_enrolled=structure.class_name, is_active=True)
            student_fees = []
            for student in students:
                # Check if already exists to avoid duplicates
                if not StudentFee.objects.filter(student=student, fee_structure=structure).exists():
                    student_fees.append(StudentFee(student=student, fee_structure=structure))
            
            if student_fees:
                StudentFee.objects.bulk_create(student_fees)
                
            messages.success(request, f'Fee structure created and assigned to {len(student_fees)} students.')
            return redirect('fee_dashboard')
    else:
        form = FeeStructureForm()
    
    return render(request, 'fees/fee_structure_form.html', {'form': form, 'title': 'Create Fee Structure'})

@login_required
@user_passes_test(is_admin)
def student_fee_list(request):
    student_fees = StudentFee.objects.select_related('student__user', 'student__class_enrolled', 'fee_structure__fee_type')
    
    # Filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    class_filter = request.GET.get('class_id', '')
    
    if search_query:
        student_fees = student_fees.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )
    
    if status_filter:
        student_fees = student_fees.filter(status=status_filter)
        
    if class_filter:
        student_fees = student_fees.filter(student__class_enrolled_id=class_filter)
        
    # Pagination
    paginator = Paginator(student_fees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    classes = Class.objects.all()
    
    context = {
        'student_fees': page_obj,
        'classes': classes,
        'search_query': search_query,
        'status_filter': status_filter,
        'class_filter': class_filter,
    }
    return render(request, 'fees/student_fee_list.html', context)

@login_required
@user_passes_test(is_admin)
def record_payment(request, student_fee_id):
    student_fee = get_object_or_404(StudentFee, id=student_fee_id)
    
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.student_fee = student_fee
            payment.recorded_by = request.user
            
            # Validation: Don't allow overpayment
            if payment.amount > student_fee.balance:
                messages.error(request, f'Amount exceeds balance. Maximum payable is {student_fee.balance}')
            else:
                payment.save()
                
                # Update StudentFee status
                student_fee.amount_paid += payment.amount
                student_fee.last_payment_date = payment.date
                
                if student_fee.amount_paid >= student_fee.fee_structure.amount:
                    student_fee.status = 'Paid'
                elif student_fee.amount_paid > 0:
                    student_fee.status = 'Partial'
                
                student_fee.save()
                
                messages.success(request, 'Payment recorded successfully!')
                return redirect('payment_receipt', payment_id=payment.id)
    else:
        # Pre-fill amount with balance
        form = FeePaymentForm(initial={'amount': student_fee.balance})
    
    context = {
        'form': form,
        'student_fee': student_fee,
        'student': student_fee.student,
    }
    return render(request, 'fees/payment_form.html', context)

@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    # Check permissions (Admin or the student themselves)
    if request.user.user_type != 'admin':
        try:
            student = Student.objects.get(user=request.user)
            if payment.student_fee.student != student:
                messages.error(request, "Permission denied.")
                return redirect('dashboard')
        except Student.DoesNotExist:
            messages.error(request, "Permission denied.")
            return redirect('dashboard')
            
    return render(request, 'fees/receipt.html', {'payment': payment})

@login_required
@user_passes_test(is_admin)
def fee_type_create(request):
    if request.method == 'POST':
        form = FeeTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee Type added successfully.')
            return redirect('fee_dashboard')
    return redirect('fee_dashboard')
