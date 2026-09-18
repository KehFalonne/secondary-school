from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Student
from .forms import StudentRegistrationForm, StudentUpdateForm
from attendance.models import Attendance
from grades.models import Grade
import datetime

def is_admin_or_teacher(user):
    return user.user_type in ['admin', 'teacher']

@login_required
@user_passes_test(is_admin_or_teacher)
def student_list(request):
    students = Student.objects.select_related('user', 'class_enrolled').filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    class_filter = request.GET.get('class', '')
    gender_filter = request.GET.get('gender', '')
    
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(father_name__icontains=search_query)
        )
    
    if class_filter:
        students = students.filter(class_enrolled_id=class_filter)
    
    if gender_filter:
        students = students.filter(user__gender=gender_filter)
    
    # Pagination
    paginator = Paginator(students, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    from courses.models import Class
    classes = Class.objects.all()
    
    context = {
        'students': page_obj,
        'classes': classes,
        'search_query': search_query,
        'class_filter': class_filter,
        'gender_filter': gender_filter,
    }
    return render(request, 'students/student_list.html', context)

@login_required
def student_detail(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    
    # Check permissions
    if not (request.user.user_type in ['admin', 'teacher'] or 
            request.user == student.user or 
            request.user == student.parent):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    # Get attendance records
    attendance = Attendance.objects.filter(student=student).order_by('-date')[:30]
    
    # Get grades
    grades = Grade.objects.filter(student=student).select_related('exam', 'exam__subject')
    
    # Calculate statistics
    total_attendance = attendance.count()
    present_count = Attendance.objects.filter(status='Present').count()
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    context = {
        'student': student,
        'attendance': attendance,
        'grades': grades,
        'attendance_percentage': attendance_percentage,
        'total_attendance': total_attendance,
        'present_count': present_count,
    }
    
    return render(request, 'students/student_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def student_create(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student created successfully!')
            return redirect('student_list')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add New Student'})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def student_update(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    
    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_detail', admission_number=admission_number)
    else:
        form = StudentUpdateForm(instance=student)
    
    return render(request, 'students/student_form.html', {
        'form': form, 
        'title': f'Update {student.user.get_full_name()}',
        'student': student,
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def student_delete(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    
    if request.method == 'POST':
        student.is_active = False
        student.leaving_date = datetime.date.today()
        student.save()
        messages.success(request, 'Student marked as inactive.')
        return redirect('student_list')
    
    return render(request, 'students/student_confirm_delete.html', {'student': student})