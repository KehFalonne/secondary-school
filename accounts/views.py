from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import models
from django.db.models import Q
from .forms import CustomPasswordChangeForm, CustomUserCreationForm, CustomUserChangeForm, LoginForm, SchoolSettingsForm, AccessRequestForm, AdminAccessRequestForm
from .models import SchoolSettings, AccessRequest, User
from .email_utils import send_approval_email, send_rejection_email, send_credential_email
from django.views.decorators.http import require_http_methods
from students.models import Student
from teachers.models import Teacher
from courses.models import Class
from attendance.models import Attendance
from grades.models import Grade, Exam
import datetime


@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def register(request):
    """Admin-only user registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.get_full_name()}.')
            return redirect('access_request_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def landing(request):
     # Example data (replace with actual data from your models)
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_courses = Class.objects.count()
    school_settings = SchoolSettings.objects.first()

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'school_settings': school_settings,
    }
    return render(request, 'accounts/landing.html', context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    context = {}
    today = datetime.date.today()
    
    if request.user.user_type == 'admin':
        # Here is the admin dashboard logic
        from django.db.models import Count, Sum, Q
       # from fees.models import FeePayment
        
        # Calculate attendance breakdown by status for today
        total_students = Student.objects.filter(is_active=True).count()
        today_attendance_records = Attendance.objects.filter(date=today)
        present_count = today_attendance_records.filter(status='Present').count()
        late_count = today_attendance_records.filter(status='Late').count()
        half_day_count = today_attendance_records.filter(status='Half Day').count()
        absent_count = today_attendance_records.filter(status='Absent').count()
        excused_count = today_attendance_records.filter(status='Excused').count()
        sick_count = today_attendance_records.filter(status='Sick').count()
        
        # Calculate attendance rate: (Present + Late + Half Day) / total_students * 100
        marked_present_like = present_count + late_count + half_day_count
        attendance_rate = round((marked_present_like / total_students * 100) if total_students > 0 else 0)
        
        context.update({
            'total_students': total_students,
            'total_teachers': Teacher.objects.filter(is_active=True).count(),
            'total_classes': Class.objects.count(),
            'today_attendance': today_attendance_records.count(),
            'attendance_rate': attendance_rate,
            'present_count': present_count,
            'late_count': late_count,
            'half_day_count': half_day_count,
            'absent_count': absent_count,
            'excused_count': excused_count,
            'sick_count': sick_count,
          #  'pending_fees': FeePayment.objects.filter(status='Pending').aggregate(Sum('amount'))['amount__sum'] or 0,
            'recent_students': Student.objects.select_related('user', 'class_enrolled').filter(is_active=True).order_by('-admission_date')[:5],
            'upcoming_exams': Exam.objects.filter(date_conducted__gte=today).order_by('date_conducted')[:5],
        })
        template = 'accounts/admin_dashboard.html'
        
    elif request.user.user_type == 'teacher':
        # Here is the teacher dashboard logic
        try:
            teacher = Teacher.objects.get(user=request.user)
            classes = Class.objects.filter(class_teacher=teacher)
            subjects = teacher.subjects.all()
            
            context.update({
                'teacher': teacher,
                'classes': classes,
                'subjects': subjects,
                'today_classes': classes.count(),
                'total_students_taught': Student.objects.filter(class_enrolled__in=classes).count(),
                'upcoming_exams': Exam.objects.filter(subject__in=subjects, date_conducted__gte=today)[:5],
            })
        except Teacher.DoesNotExist: # If the teacher profile is not found
            messages.error(request, "You are not registered as a teacher.")
            return redirect('profile')
        template = 'accounts/teacher_dashboard.html'# 
        
    elif request.user.user_type == 'student':
        # Here is the student dashboard logic
        try:
            student = Student.objects.get(user=request.user)
            grades = Grade.objects.filter(student=student)
            attendance = Attendance.objects.filter(student=student)
            
            context.update({
                'student': student,
                'grades': grades.order_by('-exam__date_conducted')[:5],
                'attendance_rate': attendance.filter(status='Present').count() / max(attendance.count(), 1) * 100,
                'recent_attendance': attendance.order_by('-date')[:5],
                'upcoming_exams': Exam.objects.filter(class_name=student.class_enrolled, date_conducted__gte=today)[:5],
            })
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('profile')
        
        template = 'accounts/student_dashboard.html'
        
    else:
        template = 'accounts/dashboard.html'
    
    return render(request, template, context)

@login_required
def profile(request):
    user = request.user
    form = CustomUserChangeForm(instance=user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # ======================
        # PROFILE DETAILS UPDATE
        # ======================
        if form_type == 'profile':
            form = CustomUserChangeForm(
                request.POST,
                request.FILES,   # ✅ IMPORTANT
                instance=user
            )
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated.')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors below.')

        # ======================
        # PROFILE PICTURE UPDATE
        # ======================
        elif form_type == 'photo':
            if request.FILES.get('profile_picture'):
                user.profile_picture = request.FILES['profile_picture']
                user.save(update_fields=['profile_picture'])
                messages.success(request, 'Profile picture updated.')
                return redirect('profile')
            else:
                messages.error(request, 'Please select an image.')

    context = {
        'form': form,
        'user': user,
        'student': Student.objects.filter(user=user).first(),
        'teacher': Teacher.objects.filter(user=user).first(),
    }

    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def system_settings(request):
    # Get the singleton instance or create it if it doesn't exist
    settings_obj, created = SchoolSettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'System settings updated successfully.')
            return redirect('system_settings')
    else:
        form = SchoolSettingsForm(instance=settings_obj)
        
    return render(request, 'accounts/system_settings.html', {'form': form})


# ==========================================
# ACCESS REQUEST VIEWS (Admin-Only Features)
# ==========================================

def request_access(request):
    """Allow users to request access to the school system"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AccessRequestForm(request.POST)
        if form.is_valid():
            access_request = form.save()
            messages.success(
                request, 
                f'Your access request has been submitted! We will review it shortly and send you a confirmation email at {access_request.email}.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AccessRequestForm()
    
    return render(request, 'accounts/request_access.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def access_request_list(request):
    """Admin view to manage access requests"""
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Start with all requests
    requests_list = AccessRequest.objects.all()
    
    # Apply filters
    if status_filter != 'all':
        requests_list = requests_list.filter(status=status_filter)
    
    if search_query:
        requests_list = requests_list.filter(
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    # Count statistics
    pending_count = AccessRequest.objects.filter(status='pending').count()
    approved_count = AccessRequest.objects.filter(status='approved').count()
    rejected_count = AccessRequest.objects.filter(status='rejected').count()
    
    context = {
        'requests': requests_list,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'current_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'accounts/access_request_list.html', context)


@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def access_request_detail(request, pk):
    """View and manage a single access request"""
    access_request = AccessRequest.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = AdminAccessRequestForm(request.POST, instance=access_request)
        if form.is_valid():
            form.save()
            
            if access_request.status == 'approved':
                # Create user account
                try:
                    # Generate username from email
                    email_prefix = access_request.email.split('@')[0]
                    username = email_prefix
                    
                    # Ensure unique username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{email_prefix}{counter}"
                        counter += 1
                    
                    # Generate temporary password
                    temp_password = User.objects.make_random_password()
                    
                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        email=access_request.email,
                        password=temp_password,
                        first_name=access_request.first_name,
                        last_name=access_request.last_name,
                        user_type=access_request.user_type,
                        phone=access_request.phone,
                    )
                    
                    # Update approval info
                    access_request.approved_by = request.user
                    access_request.approved_at = datetime.datetime.now()
                    access_request.save()
                    
                    # Send approval email
                    email_success, email_msg = send_approval_email(access_request, user)
                    
                    # Send credentials email
                    cred_success, cred_msg = send_credential_email(user, temp_password)
                    
                    if email_success and cred_success:
                        messages.success(
                            request, 
                            f'Account created for {user.get_full_name()} (Username: {username}). Approval and credential emails sent!'
                        )
                    else:
                        messages.warning(
                            request, 
                            f'Account created, but email sending had issues. {email_msg} | {cred_msg}'
                        )
                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
                    
            elif access_request.status == 'rejected':
                # Send rejection email
                email_success, email_msg = send_rejection_email(access_request)
                messages.info(request, f'Access request rejected. {email_msg}')
            
            return redirect('access_request_list')
    else:
        form = AdminAccessRequestForm(instance=access_request)
    
    context = {
        'access_request': access_request,
        'form': form,
    }
    
    return render(request, 'accounts/access_request_detail.html', context)


@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def approve_access_request(request, pk):
    """Quick approve an access request"""
    access_request = AccessRequest.objects.get(pk=pk)
    
    try:
        # Generate username from email
        email_prefix = access_request.email.split('@')[0]
        username = email_prefix
        
        # Ensure unique username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{email_prefix}{counter}"
            counter += 1
        
        # Generate temporary password
        temp_password = User.objects.make_random_password()
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=access_request.email,
            password=temp_password,
            first_name=access_request.first_name,
            last_name=access_request.last_name,
            user_type=access_request.user_type,
            phone=access_request.phone,
        )
        
        # Update access request
        access_request.status = 'approved'
        access_request.approved_by = request.user
        access_request.approved_at = datetime.datetime.now()
        access_request.save()
        
        # Send approval email
        email_success, email_msg = send_approval_email(access_request, user)
        
        # Send credentials email
        cred_success, cred_msg = send_credential_email(user, temp_password)
        
        if email_success and cred_success:
            messages.success(
                request, 
                f'Account created for {user.get_full_name()} (Username: {username}). Emails sent!'
            )
        else:
            messages.warning(
                request, 
                f'Account created, but email issues occurred. {email_msg} | {cred_msg}'
            )
    except Exception as e:
        messages.error(request, f'Error approving request: {str(e)}')
    
    return redirect('access_request_list')


@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def reject_access_request(request, pk):
    """Quick reject an access request"""
    access_request = AccessRequest.objects.get(pk=pk)
    
    # Set status to rejected if not already
    if access_request.status == 'pending':
        access_request.status = 'rejected'
        access_request.save()
    
    # Send rejection email
    email_success, email_msg = send_rejection_email(access_request)
    
    messages.info(
        request, 
        f'Access request rejected. {email_msg}'
    )
    
    return redirect('access_request_list')


@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_staff)
def email_management(request):
    """Admin page to manage and resend notification emails"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    # Start with all requests
    requests_list = AccessRequest.objects.select_related('approved_by').all().order_by('-created_at')

    # Apply filters
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    
    if search_query:
        requests_list = requests_list.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    pending_count = AccessRequest.objects.filter(status='pending').count()
    
    # Handle resend email actions
    if request.method == 'POST':
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        
        try:
            access_request = AccessRequest.objects.get(pk=request_id)
            
            if action == 'resend_approval':
                if access_request.status == 'approved' and access_request.approved_by:
                    # Get the user associated with this request
                    try:
                        user = User.objects.get(email=access_request.email)
                        email_success, email_msg = send_approval_email(access_request, user)
                        if email_success:
                            messages.success(request, f'Approval email resent to {access_request.email}')
                        else:
                            messages.error(request, f'Failed to resend: {email_msg}')
                    except User.DoesNotExist:
                        messages.error(request, f'User not found for this email: {access_request.email}')
                else:
                    messages.warning(request, 'This request is not approved yet.')
            
            elif action == 'resend_rejection':
                if access_request.status == 'rejected':
                    email_success, email_msg = send_rejection_email(access_request)
                    if email_success:
                        messages.success(request, f'Rejection email resent to {access_request.email}')
                    else:
                        messages.error(request, f'Failed to resend: {email_msg}')
                else:
                    messages.warning(request, 'This request is not rejected.')
            
            elif action == 'resend_credentials':
                if access_request.status == 'approved':
                    try:
                        user = User.objects.get(email=access_request.email)
                        temp_password = User.objects.make_random_password()
                        email_success, email_msg = send_credential_email(user, temp_password)
                        if email_success:
                            messages.success(request, f'Credentials email resent to {access_request.email}')
                        else:
                            messages.error(request, f'Failed to resend: {email_msg}')
                    except User.DoesNotExist:
                        messages.error(request, f'User not found for this email: {access_request.email}')
                else:
                    messages.warning(request, 'This request is not approved yet.')
        
        except AccessRequest.DoesNotExist:
            messages.error(request, 'Access request not found.')
        
        return redirect('email_management')
    
    context = {
        'requests': requests_list,
        'pending_count': pending_count,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'accounts/email_management.html', context)
