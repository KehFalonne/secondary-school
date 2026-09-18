from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserChangeForm 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Teacher
from accounts.models import User
from .forms import TeacherRegistrationForm, TeacherUpdateForm
from students.models import Student
from attendance.models import Attendance
from grades.models import Grade
import datetime

def is_admin(user):
    return user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def teacher_list(request):
    teachers = Teacher.objects.select_related('user').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    designation_filter = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if designation_filter:
        teachers = teachers.filter(designation=designation_filter)
    
    if status_filter == 'active':
        teachers = teachers.filter(is_active=True)
    elif status_filter == 'inactive':
        teachers = teachers.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(teachers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'teachers': page_obj,
        'search_query': search_query,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
    }
    return render(request, 'teachers/teacher_list.html', context)

@login_required
def teacher_detail(request, employee_id):
    teacher = get_object_or_404(Teacher, employee_id=employee_id)
    
    # Check permissions
    if not (request.user.user_type in ['admin', 'teacher'] or 
            request.user == teacher.user):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    # Get classes taught by this teacher
    classes_taught = teacher.classes_taught
    
    # Get subjects taught
    subjects = teacher.subjects.all()
    
    # Get timetable entries for this teacher
    from courses.models import Timetable
    timetable_entries = Timetable.objects.filter(teacher=teacher).select_related(
        'class_name', 'subject'
    ).order_by('day', 'period')
    
    # Get students taught by this teacher
    from students.models import Student
    students_taught = Student.objects.filter(
        class_enrolled__in=classes_taught
    ).distinct().count()
    
    # If class teacher, get class students
    class_students = None
    if teacher.is_class_teacher and teacher.class_teacher_of:
        class_students = Student.objects.filter(
            class_enrolled=teacher.class_teacher_of
        ).order_by('roll_number')
    
    # Get attendance records for classes taught (if teacher has access)
    attendance_stats = None
    if request.user.user_type in ['admin', 'teacher']:
        attendance_records = Attendance.objects.filter(
            student__class_enrolled__in=classes_taught
        )
        total_attendance = attendance_records.count()
        present_count = attendance_records.filter(status='Present').count()
        attendance_stats = {
            'total': total_attendance,
            'present': present_count,
            'absent': total_attendance - present_count,
            'percentage': (present_count / total_attendance * 100) if total_attendance > 0 else 0
        }
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'classes_taught': classes_taught,
        'timetable_entries': timetable_entries,
        'students_taught': students_taught,
        'class_students': class_students,
        'attendance_stats': attendance_stats,
    }
    
    return render(request, 'teachers/teacher_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def teacher_create(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher created successfully!')
            return redirect('teacher_list')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'teachers/teacher_form.html', {
        'form': form, 
        'title': 'Add New Teacher'
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')

@login_required
def teacher_update(request, employee_id):
    teacher = get_object_or_404(Teacher, employee_id=employee_id)
    
    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('teacher_detail', employee_id=teacher.employee_id)
    else:
        form = TeacherUpdateForm(instance=teacher)
    
    context = {
        'form': form,
        'teacher': teacher,
        'title': f'Edit Teacher - {teacher.employee_id}'
    }
    return render(request, 'teachers/teacher_form.html', context)



@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def teacher_delete(request, employee_id):
    teacher = get_object_or_404(Teacher, employee_id=employee_id)
    
    if request.method == 'POST':
        teacher.is_active = False
        teacher.leaving_date = datetime.date.today()
        teacher.save()
        messages.success(request, 'Teacher marked as inactive.')
        return redirect('teacher_list')
    
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})
