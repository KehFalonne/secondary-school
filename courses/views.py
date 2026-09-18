from datetime import date, time, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.apps import apps
from .models import Class, Subject, Timetable
from teachers.models import Teacher
from .forms import ClassForm, SubjectForm, TimetableForm




def is_admin_or_teacher(user):
    return user.user_type in ['admin', 'teacher']

@login_required
@user_passes_test(is_admin_or_teacher)
def class_list(request):
    classes = Class.objects.annotate(
        student_count=Count('students')
    ).order_by('name', 'section')
    
    # RBAC: Filter classes for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            timetable_class_ids = Timetable.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
            classes = classes.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
        except Exception:
            classes = Class.objects.none()

    context = {
        'classes': classes,
        'total_students': sum(c.student_count for c in classes),
        'total_teachers': Class.objects.values('class_teacher').distinct().count(),
        'total_subjects': Subject.objects.count(),
    }
    
    return render(request, 'courses/class_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def class_detail(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    
    # Get male and female student counts
    male_students = class_obj.students.filter(user__gender='Male').count()
    female_students = class_obj.students.filter(user__gender='Female').count()
    
    context = {
        'class': class_obj,
        'male_students': male_students,
        'female_students': female_students,
    }
    
    return render(request, 'courses/class_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def class_create(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class {class_obj.name} created successfully!')
            return redirect('class_detail', class_id=class_obj.id)
    else:
        form = ClassForm()
    
    return render(request, 'courses/class_form.html', {'form': form, 'title': 'Create New Class'})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def class_update(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated successfully!')
            return redirect('class_detail', class_id=class_id)
    else:
        form = ClassForm(instance=class_obj)
    
    return render(request, 'courses/class_form.html', {
        'form': form,
        'title': f'Update {class_obj.name}',
        'class': class_obj,
    })

@login_required
@user_passes_test(is_admin_or_teacher)
def subject_list(request):
    subjects = Subject.objects.annotate(
        teacher_count=Count('teachers'),
        class_count=Count('classes')
    ).order_by('name')
    
    # RBAC: Filter subjects for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            timetable_subject_ids = Timetable.objects.filter(teacher=teacher).values_list('subject_id', flat=True)
            subjects = subjects.filter(id__in=timetable_subject_ids).distinct()
        except Exception:
            subjects = Subject.objects.none()

    search_query = request.GET.get('search', '')
    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'subjects': subjects,
        'search_query': search_query,
    }
    
    return render(request, 'courses/subject_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get statistics
    total_students = sum(c.total_students for c in subject.classes.all())
    exams_count = subject.exam_set.count()
    
    context = {
        'subject': subject,
        'total_students': total_students,
        'exams_count': exams_count,
    }
    
    return render(request, 'courses/subject_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST, request.FILES)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject {subject.name} created successfully!')
            return redirect('subject_detail', subject_id=subject.id)
    else:
        form = SubjectForm()
    
    return render(request, 'courses/subject_form.html', {'form': form, 'title': 'Create New Subject'})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def subject_update(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, request.FILES, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subject_detail', subject_id=subject_id)
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'courses/subject_form.html', {
        'form': form,
        'title': f'Update {subject.name}',
        'subject': subject,
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def subject_delete(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('subject_list')
    
    return render(request, 'courses/subject_confirm_delete.html', {'subject': subject})


@login_required
def timetable(request, class_id=None):
    classes = Class.objects.all()
    selected_class = None
    timetable_entries = Timetable.objects.none()
    
    # RBAC: Filter classes based on user type
    if request.user.user_type == 'student':
        # Students can only see their own class timetable
        try:
            Student = apps.get_model('students', 'Student')
            student = Student.objects.get(user=request.user)
            if student.class_enrolled:
                classes = Class.objects.filter(id=student.class_enrolled.id)
                selected_class = student.class_enrolled
        except Exception:
            classes = Class.objects.none()
    
    elif request.user.user_type == 'teacher':
        # Teachers can see classes they teach or class they manage
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            TimetableModel = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            timetable_class_ids = TimetableModel.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
            classes = classes.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
        except Exception:
            classes = Class.objects.none()
    
    elif request.user.user_type != 'admin':
        # Only admin, teacher, and student can access
        classes = Class.objects.none()

    # GET class from dropdown (or use student's class)
    class_id = request.GET.get('class_id')

    if class_id:
        selected_class = get_object_or_404(Class, id=class_id)
        timetable_entries = Timetable.objects.filter(
            class_name=selected_class
        ).select_related(
            'teacher__user',
            'subject'
        ).order_by('day', 'period')
    elif request.user.user_type == 'student' and selected_class:
        # Auto-load student's class timetable
        timetable_entries = Timetable.objects.filter(
            class_name=selected_class
        ).select_related(
            'teacher__user',
            'subject'
        ).order_by('day', 'period')

    # PERIODS (8 × 45 minutes)
    periods = []
    start_hour = 8  # 8:00 AM

    for i in range(1, 9):
        start = time(start_hour + i - 1, 0)
        end = time(start_hour + i - 1, 45)
        periods.append({
            'number': i,
            'start_time': start,
            'end_time': end,
        })

    # DAYS (Monday → Saturday)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    days = []

    for i, name in enumerate(day_names):
        days.append({
            'name': name,
            'date': start_of_week + timedelta(days=i),
        })

    # BUILD TIMETABLE GRID (FAST + CLEAN)
    timetable_grid = {}
    for entry in timetable_entries:
        timetable_grid.setdefault(entry.day, {})[entry.period] = entry

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'periods': periods,
        'days': days,
        'timetable_grid': timetable_grid,
        'timetable_entries': timetable_entries,
        'total_hours': timetable_entries.count() * 0.75,  # 45 mins = 0.75 hr
    }

    return render(request, 'courses/timetable.html', context)



@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def timetable_form(request, class_id=None):
    classes = Class.objects.all()
    selected_class = None
    timetable_data = []
    teachers = []
    subjects = []
    
    if class_id:
        selected_class = get_object_or_404(Class, id=class_id)
        timetable_data = Timetable.objects.filter(class_name=selected_class)
        teachers = Teacher.objects.all()
        subjects = Subject.objects.all()
    
    # Days of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    if request.method == 'POST' and selected_class:
        # Save timetable entries
        Timetable.objects.filter(class_name=selected_class).delete()
        
        saved_count = 0
        
        for day in days:
            for period in range(1, 9):
                subject_id = request.POST.get(f'subject_{day}_{period}')
                teacher_id = request.POST.get(f'teacher_{day}_{period}')
                room = request.POST.get(f'room_{day}_{period}')
                
                if subject_id and teacher_id:
                    Timetable.objects.create(
                        class_name=selected_class,
                        day=day,
                        period=period,
                        subject_id=subject_id,
                        teacher_id=teacher_id,
                        room=room,
                        start_time=f'{(7+period):02d}:00',
                        end_time=f'{(7+period):02d}:45'
                    )
                    saved_count += 1
        
        if saved_count > 0:
            messages.success(request, f'Timetable for {selected_class.name} saved successfully! ({saved_count} entries)')
        else:
            messages.warning(request, 'No timetable entries were saved. For each period, you must select BOTH a Subject AND a Teacher.')
        return redirect('timetable_class', class_id=selected_class.id)
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'days': days,
        'timetable_data': timetable_data,
        'teachers': teachers,
        'subjects': subjects,
        'periods': [{'number': i, 'start_time': None, 'end_time': None} for i in range(1, 9)],
    }
    
    return render(request, 'courses/timetable_form.html', context)
