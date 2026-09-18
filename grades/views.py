from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Sum, Max, F
from .models import Exam, Grade, ReportCard
from students.models import Student
from courses.models import Class, Subject
from django.apps import apps
from decimal import Decimal, InvalidOperation
import datetime
from datetime import timedelta

def is_admin_or_teacher(user):
    return user.user_type in ['admin', 'teacher']

@login_required
@user_passes_test(is_admin_or_teacher)
def exam_list(request):
    exams = Exam.objects.select_related('subject', 'class_name', 'created_by').all()
    classes = Class.objects.all()
    subjects = Subject.objects.all()
    
    # RBAC: Filter exams for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            # 1. Classes I am class teacher of
            class_teacher_ids = Class.objects.filter(class_teacher=teacher).values_list('id', flat=True)
            
            # 2. Classes/Subjects I teach (Complex filter)
            timetable_entries = Timetable.objects.filter(teacher=teacher)
            timetable_q = Q()
            for entry in timetable_entries:
                timetable_q |= (Q(class_name=entry.class_name) & Q(subject=entry.subject))
            
            exams = exams.filter(
                Q(created_by=request.user) |
                Q(class_name__in=class_teacher_ids) |
                timetable_q
            ).distinct()
            
            # Filter dropdowns to only show relevant options
            classes = Class.objects.filter(id__in=exams.values('class_name'))
            subjects = Subject.objects.filter(id__in=exams.values('subject'))
        except Exception:
            exams = Exam.objects.none()
            classes = Class.objects.none()
            subjects = Subject.objects.none()
    
    # Filtering
    class_filter = request.GET.get('class_id')
    subject_filter = request.GET.get('subject_id')
    exam_type_filter = request.GET.get('exam_type')
    term_filter = request.GET.get('term')
    search_query = request.GET.get('search', '')
    
    if search_query:
        exams = exams.filter(
            Q(name__icontains=search_query) |
            Q(subject__name__icontains=search_query) |
            Q(class_name__name__icontains=search_query)
        )
    
    if class_filter:
        exams = exams.filter(class_name_id=class_filter)
    
    if subject_filter:
        exams = exams.filter(subject_id=subject_filter)
    
    if exam_type_filter:
        exams = exams.filter(exam_type=exam_type_filter)
    
    if term_filter:
        exams = exams.filter(term=term_filter)
    
    # Pagination
    paginator = Paginator(exams, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get upcoming exams (next 7 days)
    today = datetime.date.today()
    upcoming_date = today + timedelta(days=7)
    upcoming_exams_qs = Exam.objects.filter(
        date_conducted__gte=today,
        date_conducted__lte=upcoming_date
    )

    if request.user.user_type == 'teacher':
        try:
            # Re-use the teacher-specific query parts from above
            upcoming_exams_qs = upcoming_exams_qs.filter(
                Q(created_by=request.user) |
                Q(class_name__in=class_teacher_ids) |
                timetable_q
            ).distinct()
        except NameError: # In case the initial RBAC block failed
            upcoming_exams_qs = Exam.objects.none()
        except Exception:
            upcoming_exams_qs = Exam.objects.none()

    upcoming_exams = upcoming_exams_qs.order_by('date_conducted')[:6]


    context = {
        'exams': page_obj,
        'classes': classes,
        'subjects': subjects,
        'exam_types': Exam.EXAM_TYPES,
        'terms': Exam.TERM_CHOICES,
        'class_filter': class_filter,
        'subject_filter': subject_filter,
        'exam_type_filter': exam_type_filter,
        'term_filter': term_filter,
        'search_query': search_query,
        'upcoming_exams': upcoming_exams,
    }
    return render(request, 'grades/exam_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # RBAC: Check permission for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher_obj = Teacher.objects.get(user=request.user)

            is_class_teacher = (exam.class_name.class_teacher == teacher_obj)
            teaches_subject = Timetable.objects.filter(
                teacher=teacher_obj,
                class_name=exam.class_name,
                subject=exam.subject
            ).exists()
            created_exam = (exam.created_by == request.user)

            if not (is_class_teacher or teaches_subject or created_exam):
                messages.error(request, "You do not have permission to view this exam's details.")
                return redirect('exam_list')
        except Exception:
            pass

    grades = Grade.objects.filter(exam=exam).select_related('student', 'student__user', 'evaluated_by')
    
    # Statistics
    total_students = exam.class_name.total_students
    graded_count = grades.count()
    passed_count = grades.filter(marks_obtained__gte=exam.pass_marks).count()
    failed_count = graded_count - passed_count
    absent_count = grades.filter(is_absent=True).count()
    
    avg_marks = grades.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
    highest_marks = grades.aggregate(max=Max('marks_obtained'))['max'] or 0
    
    # Grade distribution
    grade_distribution = []
    total_graded = grades.count()
    for grade_choice, _ in Grade.GRADE_CHOICES:
        count = grades.filter(grade=grade_choice).count()
        if count > 0 or grade_choice in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']:
            grade_distribution.append({
                'grade': grade_choice,
                'count': count,
                'percentage': (count / total_graded * 100) if total_graded > 0 else 0
            })
    
    context = {
        'exam': exam,
        'grades': grades.order_by('-marks_obtained'),
        'total_students': total_students,
        'graded_count': graded_count,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'absent_count': absent_count,
        'avg_marks': avg_marks,
        'highest_marks': highest_marks,
        'grade_distribution': grade_distribution,
    }
    return render(request, 'grades/exam_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def exam_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        exam_type = request.POST.get('exam_type')
        term = request.POST.get('term', '')
        subject_id = request.POST.get('subject_id')
        class_id = request.POST.get('class_id')
        total_marks = request.POST.get('total_marks', 100)
        pass_marks = request.POST.get('pass_marks', 40)
        weightage = request.POST.get('weightage', 1.0)
        date_conducted = request.POST.get('date_conducted')
        
        if name and subject_id and class_id and date_conducted:
            exam = Exam.objects.create(
                name=name,
                exam_type=exam_type,
                term=term,
                subject_id=subject_id,
                class_name_id=class_id,
                total_marks=total_marks,
                pass_marks=pass_marks,
                weightage=weightage,
                date_conducted=date_conducted,
                created_by=request.user
            )
            messages.success(request, 'Exam created successfully!')
            return redirect('exam_detail', exam_id=exam.id)
        else:
            messages.error(request, 'Please fill all required fields.')
    
    context = {
        'classes': Class.objects.all(),
        'subjects': Subject.objects.all(),
        'exam_types': Exam.EXAM_TYPES,
        'terms': Exam.TERM_CHOICES,
    }
    return render(request, 'grades/exam_form.html', {'title': 'Create New Exam', **context})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def exam_update(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        exam.name = request.POST.get('name')
        exam.exam_type = request.POST.get('exam_type')
        exam.term = request.POST.get('term', '')
        exam.subject_id = request.POST.get('subject_id')
        exam.class_name_id = request.POST.get('class_id')
        exam.total_marks = request.POST.get('total_marks', 100)
        exam.exam_time = request.POST.get('exam_time')
        exam.pass_marks = request.POST.get('pass_marks', 40)
        exam.weightage = request.POST.get('weightage', 1.0)
        exam.date_conducted = request.POST.get('date_conducted')
        exam.save()
        
        messages.success(request, 'Exam updated successfully!')
        return redirect('exam_detail', exam_id=exam.id)
    
    context = {
        'exam': exam,
        'classes': Class.objects.all(),
        'subjects': Subject.objects.all(),
        'exam_types': Exam.EXAM_TYPES,
        'terms': Exam.TERM_CHOICES,
    }
    return render(request, 'grades/exam_form.html', {'title': f'Update {exam.name}', **context})
@login_required
@user_passes_test(is_admin_or_teacher)
def grade_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    students = Student.objects.filter(
        class_enrolled=exam.class_name,
        is_active=True
    ).order_by('roll_number')

    # RBAC: Check permission for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher_obj = Teacher.objects.get(user=request.user)
            
            is_class_teacher = (exam.class_name.class_teacher == teacher_obj)
            teaches_subject = Timetable.objects.filter(
                teacher=teacher_obj, 
                class_name=exam.class_name, 
                subject=exam.subject
            ).exists()
            created_exam = (exam.created_by == request.user)
            
            if not (is_class_teacher or teaches_subject or created_exam):
                messages.error(request, "You do not have permission to grade this exam.")
                return redirect('exam_list')
        except Exception:
            pass

    # ✅ get teacher safely
    teacher = None
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            teacher = Teacher.objects.get(user=request.user)
        except Exception:
            pass # Teacher profile might not exist, teacher remains None
            
    if request.method == 'POST':
        for student in students:
            marks_obtained = request.POST.get(f'marks_{student.pk}', '').strip()
            is_absent = request.POST.get(f'absent_{student.pk}') == 'on'
            remarks = request.POST.get(f'remarks_{student.pk}', '').strip()

            if marks_obtained != '' or is_absent:
                try:
                    marks = 0 if is_absent else Decimal(marks_obtained)
                except (ValueError, InvalidOperation):
                    marks = 0

                grade, created = Grade.objects.get_or_create(
                    student=student,
                    exam=exam,
                    defaults={
                        'marks_obtained': marks,
                        'is_absent': is_absent,
                        'remarks': remarks,
                        'evaluated_by': teacher,
                    }
                )

                if not created:
                    grade.marks_obtained = marks
                    grade.is_absent = is_absent
                    grade.remarks = remarks
                    grade.evaluated_by = teacher
                    grade.save()

        messages.success(request, 'Grades saved successfully!')
        return redirect('exam_detail', exam_id=exam.id)

    existing_grades = {
        g.student.pk: g
        for g in Grade.objects.filter(exam=exam)
    }
    
    # Attach grade to student objects for template rendering
    for student in students:
        student.grade = existing_grades.get(student.pk)

    return render(request, 'grades/grade_exam.html', {
        'exam': exam,
        'students': students,
        'existing_grades': existing_grades,
    })



@login_required
@user_passes_test(is_admin_or_teacher)
def grade_list(request):
    grades = Grade.objects.select_related(
        'student', 'student__user', 'exam', 'exam__subject', 'exam__class_name', 'evaluated_by'
    ).order_by('-exam__date_conducted')
    
    classes = Class.objects.all()
    subjects = Subject.objects.all()
    
    # RBAC: Filter grades for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            class_teacher_ids = Class.objects.filter(class_teacher=teacher).values_list('id', flat=True)
            timetable_entries = Timetable.objects.filter(teacher=teacher)
            
            timetable_q = Q()
            for entry in timetable_entries:
                timetable_q |= (Q(exam__class_name=entry.class_name) & Q(exam__subject=entry.subject))
            
            grades = grades.filter(
                Q(exam__created_by=request.user) |
                Q(exam__class_name__in=class_teacher_ids) |
                timetable_q
            ).distinct()
            
            classes = Class.objects.filter(id__in=grades.values('exam__class_name'))
            subjects = Subject.objects.filter(id__in=grades.values('exam__subject'))
        except Exception:
            grades = Grade.objects.none()
            classes = Class.objects.none()
            subjects = Subject.objects.none()
    
    # Filtering
    student_filter = request.GET.get('student_id')
    class_filter = request.GET.get('class_id')
    subject_filter = request.GET.get('subject_id')
    exam_type_filter = request.GET.get('exam_type')
    
    if student_filter:
        grades = grades.filter(student_id=student_filter)
    if class_filter:
        grades = grades.filter(exam__class_name_id=class_filter)
    if subject_filter:
        grades = grades.filter(exam__subject_id=subject_filter)
    if exam_type_filter:
        grades = grades.filter(exam__exam_type=exam_type_filter)

    # Statistics
    total_grades_count = grades.count()
    passed_grades_count = grades.filter(marks_obtained__gte=F('exam__pass_marks')).count()
    pass_percentage = (passed_grades_count / total_grades_count * 100) if total_grades_count > 0 else 0
    average_gpa = grades.aggregate(avg_gpa=Avg('grade_point'))['avg_gpa'] or 0
    top_grade = grades.order_by('-marks_obtained').first()
    top_student_name = top_grade.student.user.get_full_name() if top_grade else "N/A"
    
    # Pagination
    paginator = Paginator(grades, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'grades': page_obj,
        'students': Student.objects.filter(is_active=True),
        'classes': classes,
        'subjects': subjects,
        'exam_types': Exam.EXAM_TYPES,
        'student_filter': student_filter,
        'class_filter': class_filter,
        'subject_filter': subject_filter,
        'exam_type_filter': exam_type_filter,
        'total_grades': total_grades_count,
        'pass_percentage': pass_percentage,
        'top_student': top_student_name,
        'average_gpa': average_gpa,
    }
    return render(request, 'grades/grade_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def grade_update(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    exam = grade.exam

    # RBAC: Check permission for teachers
    if request.user.user_type == 'teacher':
        try:
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher_obj = Teacher.objects.get(user=request.user)

            is_class_teacher = (exam.class_name.class_teacher == teacher_obj)
            teaches_subject = Timetable.objects.filter(
                teacher=teacher_obj,
                class_name=exam.class_name,
                subject=exam.subject
            ).exists()
            created_exam = (exam.created_by == request.user)

            if not (is_class_teacher or teaches_subject or created_exam):
                messages.error(request, "You do not have permission to update grades for this exam.")
                return redirect('grade_list')
        except Exception:
            pass
    
    if request.method == 'POST':
        marks_obtained = request.POST.get('marks_obtained')
        is_absent = request.POST.get('is_absent') == 'on'
        remarks = request.POST.get('remarks', '')
        
        grade.marks_obtained = 0 if is_absent else Decimal(marks_obtained or 0)
        grade.is_absent = is_absent
        grade.remarks = remarks
        grade.save()
        
        messages.success(request, 'Grade updated successfully!')
        return redirect('exam_detail', exam_id=grade.exam.id)
    
    return render(request, 'grades/grade_form.html', {'grade': grade})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def exam_delete(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully!')
        return redirect('exam_list')
    
    return render(request, 'grades/exam_confirm_delete.html', {'exam': exam})


@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def grade_delete(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    
    if request.method == 'POST':
        grade.delete()
        messages.success(request, 'Grade deleted successfully!')
        return redirect('exam_list')
    
    return render(request, 'grades/grade_confirm_delete.html', {'exam': grade})