from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from students.models import Student
from courses.models import Class
from grades.models import ReportCard, Exam, Grade
from .utils import generate_report_card_pdf, generate_html_report_card, generate_bulk_report_cards as generate_bulk_report_cards_util
import datetime

@login_required
@user_passes_test(lambda u: u.user_type in ['admin', 'teacher'])
def report_card_list(request):
    report_cards = ReportCard.objects.select_related('student', 'student__user', 'class_name')
    
    # RBAC: Filter report cards and classes for teachers
    if request.user.user_type == 'teacher':
        try:
            from django.apps import apps
            Teacher = apps.get_model('teachers', 'Teacher')
            Timetable = apps.get_model('courses', 'Timetable')
            teacher = Teacher.objects.get(user=request.user)
            
            timetable_class_ids = Timetable.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
            allowed_classes = Class.objects.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
            
            report_cards = report_cards.filter(class_name__in=allowed_classes)
            classes = allowed_classes
        except Exception:
            report_cards = ReportCard.objects.none()
            classes = Class.objects.none()
    else:
        classes = Class.objects.all()

    # Filters
    class_filter = request.GET.get('class', '')
    term_filter = request.GET.get('term', '')
    year_filter = request.GET.get('year', '')
    student_filter = request.GET.get('student', '')
    
    if class_filter:
        report_cards = report_cards.filter(class_name_id=class_filter)
    
    if term_filter:
        report_cards = report_cards.filter(term=term_filter)
    
    if year_filter:
        report_cards = report_cards.filter(academic_year=year_filter)
    
    if student_filter:
        report_cards = report_cards.filter(
            Q(student__user__first_name__icontains=student_filter) |
            Q(student__user__last_name__icontains=student_filter) |
            Q(student__admission_number__icontains=student_filter)
        )
    
    current_year = f"{datetime.date.today().year}-{datetime.date.today().year + 1}"
    
    context = {
        'report_cards': report_cards.order_by('-academic_year', 'term', 'class_name'),
        'classes': classes,
        'current_year': current_year,
        'class_filter': class_filter,
        'term_filter': term_filter,
        'year_filter': year_filter,
        'student_filter': student_filter,
    }
    
    return render(request, 'reports/report_card_list.html', context)

@login_required
def student_report_cards(request, admission_number=None):
    if admission_number:
        student = get_object_or_404(Student, admission_number=admission_number)
    else:
        # For students viewing their own report cards
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('dashboard')
    
    # Check permissions
    if not (request.user.user_type in ['admin', 'teacher'] or 
            request.user == student.user or 
            request.user == student.parent):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    report_cards = ReportCard.objects.filter(student=student).order_by('-academic_year', 'term')
    
    context = {
        'student': student,
        'report_cards': report_cards,
    }
    
    return render(request, 'reports/student_report_cards.html', context)

@login_required
@user_passes_test(lambda u: u.user_type in ['admin', 'teacher'])
def generate_report_card(request, report_card_id):
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Generate PDF
    response = generate_report_card_pdf(report_card)
    
    # Mark as published
    if not report_card.is_published:
        report_card.is_published = True
        report_card.published_date = datetime.date.today()
        report_card.save()
    
    return response

@login_required
@user_passes_test(lambda u: u.user_type in ['admin', 'teacher'])
def generate_single_report_card(request, student_id, term, academic_year):
    student = get_object_or_404(Student, id=student_id)
    
    # Create or get report card
    report_card, created = ReportCard.objects.get_or_create(
        student=student,
        academic_year=academic_year,
        term=term,
        class_name=student.class_enrolled
    )
    
    # Calculate performance
    report_card.calculate_performance()
    
    # Generate PDF
    return generate_report_card(request, report_card.id)

@login_required
@user_passes_test(lambda u: u.user_type in ['admin', 'teacher'])
def generate_bulk_report_cards(request):
    if request.method == 'POST':
        academic_year = request.POST.get('academic_year')
        term = request.POST.get('term')
        class_id = request.POST.get('class_id')
        
        if academic_year and term and class_id:
            try:
                # RBAC Check for teachers
                if request.user.user_type == 'teacher':
                    from django.apps import apps
                    Teacher = apps.get_model('teachers', 'Teacher')
                    Timetable = apps.get_model('courses', 'Timetable')
                    teacher = Teacher.objects.get(user=request.user)
                    
                    timetable_class_ids = Timetable.objects.filter(teacher=teacher).values_list('class_name_id', flat=True)
                    allowed_classes = Class.objects.filter(Q(id__in=timetable_class_ids) | Q(class_teacher=teacher)).distinct()
                    
                    if int(class_id) not in allowed_classes.values_list('id', flat=True):
                        messages.error(request, "You do not have permission to generate reports for this class.")
                        return redirect('report_card_list')

                class_obj = get_object_or_404(Class, id=class_id)
                generate_bulk_report_cards_util(academic_year, term, class_obj)
                messages.success(request, "Report cards generation started successfully.")
            except Exception as e:
                messages.error(request, f"Error generating report cards: {str(e)}")
        else:
            messages.error(request, "Please provide all required fields.")
            
    return redirect('report_card_list')