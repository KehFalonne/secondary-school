from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.apps import apps
from django.urls import reverse
from urllib.parse import urlencode
from datetime import datetime, timedelta
from .models import Attendance, AttendanceReport
from students.models import Student
from courses.models import Class, Subject
from .forms import BulkAttendanceForm

def is_admin_or_teacher(user):
    return user.user_type in ['admin', 'teacher']

@login_required
@user_passes_test(is_admin_or_teacher)
def take_attendance(request):
    today = datetime.now().date()
    
    # RBAC: Filter classes based on user role
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            # Classes where teacher is class teacher OR teaches a subject
            timetable_class_ids = Timetable.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
            classes = Class.objects.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
        except Exception:
            classes = Class.objects.none()
    else:
        classes = Class.objects.all()
        
    students = []
    selected_class = None
    selected_subject = None
    selected_date = today
    
    # Initialize form with GET data if available, otherwise empty
    # We don't bind POST data here because the main action is saving student status
    form = BulkAttendanceForm(request.GET or {'date': today})
    form.fields['class_id'].queryset = classes  # Apply RBAC to form validation

    # =========================
    # GET REQUEST (DISPLAY)
    # =========================
    if request.method == "GET" and form.is_valid():
        selected_date = form.cleaned_data['date']
        selected_class = form.cleaned_data['class_id']
        selected_subject = form.cleaned_data['subject_id']

        if selected_class:
            students = Student.objects.filter(
                class_enrolled=selected_class,
                is_active=True
            ).order_by("roll_number")

            attendance_qs = Attendance.objects.filter(
                student__in=students,
                date=selected_date,
                subject=selected_subject,   # None for daily attendance
                period=None
            )

            attendance_map = {a.student_id: a for a in attendance_qs}
            for student in students:
                student.attendance_record = attendance_map.get(student.pk)

    # =========================
    # POST REQUEST (SAVE)
    # =========================
    if request.method == "POST":
        # Validate the header info using the form again
        form = BulkAttendanceForm(request.POST)
        form.fields['class_id'].queryset = classes  # Apply RBAC to form validation
        
        if not form.is_valid():
            messages.error(request, "Invalid form data. Please check class and date.")
            return redirect("take_attendance")

        date = form.cleaned_data['date']
        selected_class = form.cleaned_data['class_id']
        selected_subject = form.cleaned_data['subject_id']
        
        students = Student.objects.filter(
            class_enrolled=selected_class,
            is_active=True
        ).order_by("roll_number")

        saved_count = 0
        
        # Get Teacher instance if the user is a teacher
        teacher_instance = None
        if request.user.user_type == 'teacher':
            try:
                from teachers.models import Teacher
                teacher_instance = Teacher.objects.get(user=request.user)
            except Exception:
                pass

        for student in students:
            status = request.POST.get(f"status_{student.pk}")
            remarks = request.POST.get(f"remarks_{student.pk}", "")

            if not status:
                continue

            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=date,
                subject=selected_subject,  # None = daily attendance
                period=None,
                defaults={
                    "status": status,
                    "remarks": remarks,
                    "marked_by": request.user,
                    "teacher": teacher_instance,
                },
            )

            saved_count += 1

        messages.success(request, f"Attendance saved for {saved_count} students.")

        query_params = {
            "class_id": selected_class.id,
            "date": date.isoformat(),
        }
        if selected_subject:
            query_params["subject_id"] = selected_subject.id

        return redirect(f"{reverse('take_attendance')}?{urlencode(query_params)}")

    # =========================
    # RECENT ATTENDANCE
    # =========================
    recent_attendance = []
    if selected_class:
        recent_dates = (
            Attendance.objects.filter(
                student__class_enrolled=selected_class,
                date__lte=today,
            )
            .values("date")
            .distinct()
            .order_by("-date")[:5]
        )

        for item in recent_dates:
            date = item["date"]
            records = Attendance.objects.filter(
                student__class_enrolled=selected_class,
                date=date,
                
            )

            total = records.count()
            present = records.filter(status="Present").count()
            absent = records.filter(status="Absent").count()
            percentage = (present / total * 100) if total else 0

            recent_attendance.append({
                "date": date,
                "present_count": present,
                "absent_count": absent,
                "total_count": total,
                "percentage": percentage,
                "subject": records.first().subject if records.exists() else None,
                "marked_by": records.first().marked_by if records.exists() else None,
            })

    # Determine available subjects for the selected class based on role
    available_subjects = []
    if selected_class:
        if request.user.user_type == 'teacher':
            try:
                Teacher = apps.get_model('teachers', 'Teacher')
                Timetable = apps.get_model('courses', 'Timetable')
                teacher = Teacher.objects.get(user=request.user)
                
                # Subjects taught by this teacher in this class
                subject_ids = Timetable.objects.filter(
                    teacher=teacher, 
                    class_name=selected_class
                ).values_list('subject_id', flat=True)
                available_subjects = Subject.objects.filter(id__in=subject_ids)
            except Exception:
                available_subjects = []
        else:
            available_subjects = Subject.objects.all()

    context = {
        "form": form,
        "today": today,
        "classes": classes,
        "students": students,
        "selected_class": selected_class,
        "selected_subject": selected_subject,
        "subjects": available_subjects,
        "selected_date": selected_date,
        "status_choices": Attendance.STATUS_CHOICES,
        "recent_attendance": recent_attendance,
    }

    return render(request, "attendance/take_attendance.html", context)


@login_required
@user_passes_test(is_admin_or_teacher)
def attendance_list(request):
    attendance_records = Attendance.objects.select_related('student', 'student__user', 
                                                         'subject', 'teacher', 'marked_by').all()
    
    # RBAC: Filter records and classes
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            timetable_class_ids = Timetable.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
            allowed_classes = Class.objects.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
            
            # Filter records: Students in allowed classes OR records marked by this teacher
            attendance_records = attendance_records.filter(
                Q(student__class_enrolled__in=allowed_classes) | 
                Q(teacher=teacher) |
                Q(marked_by=request.user)
            )
            classes = allowed_classes
            students = Student.objects.filter(class_enrolled__in=allowed_classes, is_active=True)
        except Exception:
            attendance_records = Attendance.objects.none()
            classes = Class.objects.none()
            students = Student.objects.none()
    else:
        classes = Class.objects.all()
        students = Student.objects.filter(is_active=True)

    # Filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    class_filter = request.GET.get('class_id')
    student_filter = request.GET.get('student_id')
    
    if start_date and end_date:
        attendance_records = attendance_records.filter(date__range=[start_date, end_date])
    
    if class_filter:
        attendance_records = attendance_records.filter(student__class_enrolled_id=class_filter)
    
    if student_filter:
        attendance_records = attendance_records.filter(student_id=student_filter)
    
    # Statistics
    total_present = attendance_records.filter(status='Present').count()
    total_absent = attendance_records.filter(status='Absent').count()
    total_late = attendance_records.filter(status='Late').count()
    total_records = attendance_records.count()
    overall_percentage = (total_present / total_records * 100) if total_records > 0 else 0
    
    # Pagination
    paginator = Paginator(attendance_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'attendance_records': page_obj,
        'classes': classes,
        'students': students,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'overall_percentage': overall_percentage,
        'start_date': start_date,
        'end_date': end_date,
        'class_filter': class_filter,
        'student_filter': student_filter,
    }
    
    return render(request, 'attendance/attendance_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def attendance_report(request):
    report_type = request.GET.get('report_type', 'student')
    student_id = request.GET.get('student_id')
    class_id = request.GET.get('class_id')
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    # Convert student_id and class_id to integers if provided
    if student_id:
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            student_id = None
    
    if class_id:
        try:
            class_id = int(class_id)
        except (ValueError, TypeError):
            class_id = None
    
    report_data = {}
    report_title = ""
    report_period = f"{datetime(year, month, 1).strftime('%B %Y')}"
    
    # RBAC: Filter classes and validate access
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            timetable_class_ids = Timetable.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
            allowed_classes = Class.objects.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
            classes = allowed_classes
            
            # Validate class access
            if class_id and int(class_id) not in allowed_classes.values_list('id', flat=True):
                messages.error(request, "You do not have permission to view reports for this class.")
                return redirect('attendance_report')
            
            # Validate student access
            if student_id:
                student_obj = get_object_or_404(Student, id=student_id)
                if student_obj.class_enrolled not in allowed_classes:
                    messages.error(request, "You do not have permission to view reports for this student.")
                    return redirect('attendance_report')
            
            students = Student.objects.filter(class_enrolled__in=allowed_classes, is_active=True).order_by('user__first_name', 'user__last_name')
        except Exception:
            classes = Class.objects.none()
            students = Student.objects.none()
    else:
        classes = Class.objects.all()
        students = Student.objects.filter(is_active=True).order_by('user__first_name', 'user__last_name')

    if report_type == 'student':
        # Student-wise report - show selected student or ALL students
        all_students = students
        
        # If a specific student is selected, filter to that student only
        if student_id:
            try:
                selected_student = get_object_or_404(Student, id=student_id)
                students_to_report = Student.objects.filter(id=student_id)
                report_title = f"Student-wise Attendance Report - {selected_student.user.get_full_name()}"
            except Exception as e:
                # If student not found, show all
                students_to_report = students
                report_title = "Student-wise Attendance Report"
        else:
            students_to_report = students
            report_title = "Student-wise Attendance Report"
        
        # Keep original students queryset for dropdown
        
        student_data = []
        for student in students_to_report:
            attendance = Attendance.objects.filter(
                student=student,
                date__year=year,
                date__month=month
            )
            
            present = attendance.filter(status='Present').count()
            absent = attendance.filter(status='Absent').count()
            late = attendance.filter(status='Late').count()
            half_day = attendance.filter(status='Half Day').count()
            total = attendance.count()
            
            effective_present = present + late + (half_day * 0.5)
            percentage = (effective_present / total * 100) if total > 0 else 0
            
            # Get daily attendance for details
            daily_attendance = []
            for record in attendance.order_by('date'):
                daily_attendance.append({
                    'date': record.date,
                    'status': record.status,
                    'subject': record.subject.name if record.subject else 'All Day',
                    'teacher': record.teacher.user.get_full_name() if record.teacher else '',
                    'remarks': record.remarks,
                })
            
            student_data.append({
                'student': student,
                'name': student.user.get_full_name(),
                'admission_number': student.admission_number,
                'roll_number': student.roll_number,
                'class': student.class_enrolled.name,
                'present': present,
                'absent': absent,
                'late': late,
                'half_day': half_day,
                'total': total,
                'percentage': percentage,
                'daily_attendance': daily_attendance,
            })
        
        # Calculate overall statistics
        total_present = sum(s['present'] for s in student_data)
        total_absent = sum(s['absent'] for s in student_data)
        avg_attendance = sum(s['percentage'] for s in student_data) / len(student_data) if student_data else 0
        below_75 = sum(1 for s in student_data if s['percentage'] < 75)
        below_50 = sum(1 for s in student_data if s['percentage'] < 50)
        
        report_data = {
            'students': student_data,
            'total_present': total_present,
            'total_absent': total_absent,
            'average_attendance': avg_attendance,
            'below_75_percent': below_75,
            'below_50_percent': below_50,
        }
        
        context = {
            'report_type': report_type,
            'report_title': report_title,
            'report_period': report_period,
            'report_data': report_data,
            'students': all_students,
            'classes': classes,
            'months': [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
            'years': range(datetime.now().year - 5, datetime.now().year + 1),
            'current_month': month,
            'current_year': year,
            'selected_student_id': student_id,
        }
        
    elif report_type == 'class' and class_id:
        class_obj = get_object_or_404(Class, id=class_id)
        report_title = f"Class Report - {class_obj.name}"
        
        # Get all students in class
        students = Student.objects.filter(class_enrolled=class_obj, is_active=True)
        
        # Calculate statistics for each student
        student_data = []
        for student in students:
            attendance = Attendance.objects.filter(
                student=student,
                date__year=year,
                date__month=month
            )
            
            present = attendance.filter(status='Present').count()
            absent = attendance.filter(status='Absent').count()
            late = attendance.filter(status='Late').count()
            half_day = attendance.filter(status='Half Day').count()
            total = attendance.count()
            
            effective_present = present + late + (half_day * 0.5)
            percentage = (effective_present / total * 100) if total > 0 else 0
            
            student_data.append({
                'name': student.user.get_full_name(),
                'roll_number': student.roll_number,
                'present': present,
                'absent': absent,
                'late': late,
                'percentage': percentage,
            })
        
        # Class statistics
        total_students = students.count()
        avg_attendance = sum(s['percentage'] for s in student_data) / total_students if total_students > 0 else 0
        below_75 = sum(1 for s in student_data if s['percentage'] < 75)
        below_50 = sum(1 for s in student_data if s['percentage'] < 50)
        
        report_data = {
            'total_students': total_students,
            'average_attendance': avg_attendance,
            'below_75_percent': below_75,
            'below_50_percent': below_50,
            'students': student_data,
        }
        
        context = {
            'report_type': report_type,
            'report_title': report_title,
            'report_period': report_period,
            'report_data': report_data,
            'class_obj': class_obj,
            'students': students,
            'classes': classes,
            'months': [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
            'years': range(datetime.now().year - 5, datetime.now().year + 1),
            'current_month': month,
            'current_year': year,
        }
        
    else:
        # Monthly summary report
        report_title = "Monthly Summary Report"
        
        class_data = []
        
        for class_obj in classes:
            students = Student.objects.filter(class_enrolled=class_obj, is_active=True)
            if not students.exists():
                continue
            
            # Calculate class statistics
            class_stats = []
            for student in students:
                attendance = Attendance.objects.filter(
                    student=student,
                    date__year=year,
                    date__month=month
                )
                present = attendance.filter(status='Present').count()
                late = attendance.filter(status='Late').count()
                half_day = attendance.filter(status='Half Day').count()
                total = attendance.count()
                
                effective_present = present + late + (half_day * 0.5)
                percentage = (effective_present / total * 100) if total > 0 else 0
                class_stats.append(percentage)
            
            avg_attendance = sum(class_stats) / len(class_stats) if class_stats else 0
            below_75 = sum(1 for p in class_stats if p < 75)
            below_50 = sum(1 for p in class_stats if p < 50)
            
            class_data.append({
                'name': f"{class_obj.name} - {class_obj.section}",
                'total_students': students.count(),
                'working_days': 22,  # This would be calculated from school calendar
                'avg_present': avg_attendance * students.count() / 100 if students.count() > 0 else 0,
                'avg_absent': students.count() - (avg_attendance * students.count() / 100),
                'attendance_percentage': avg_attendance,
                'below_75_percent': below_75,
                'below_50_percent': below_50,
            })
        
        # Calculate totals
        totals = {
            'total_students': sum(c['total_students'] for c in class_data),
            'working_days': 22,
            'avg_present': sum(c['avg_present'] for c in class_data) / len(class_data) if class_data else 0,
            'avg_absent': sum(c['avg_absent'] for c in class_data) / len(class_data) if class_data else 0,
            'avg_attendance': sum(c['attendance_percentage'] for c in class_data) / len(class_data) if class_data else 0,
            'total_below_75': sum(c['below_75_percent'] for c in class_data),
            'total_below_50': sum(c['below_50_percent'] for c in class_data),
        }
        
        report_data = {
            'classes': class_data,
            'totals': totals,
        }
        
        context = {
            'report_type': report_type,
            'report_title': report_title,
            'report_period': report_period,
            'report_data': report_data,
            'students': students,
            'classes': classes,
            'months': [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
            'years': range(datetime.now().year - 5, datetime.now().year + 1),
            'current_month': month,
            'current_year': year,
        }
    
    return render(request, 'attendance/attendance_report.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def update_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks')
        
        attendance.status = status
        attendance.remarks = remarks
        attendance.save()
        
        messages.success(request, 'Attendance updated successfully!')
        return redirect('attendance_list')
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def delete_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if request.method == 'POST':
        attendance.delete()
        messages.success(request, 'Attendance record deleted successfully!')
        return redirect('attendance_list')
    
    return render(request, 'attendance/attendance_confirm_delete.html', {'attendance': attendance})
