import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import datetime

def generate_report_card_pdf(report_card):
    """Generate PDF report card"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Report_Card_{report_card.student.admission_number}_{report_card.term}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    
    # School Header
    school_info = [
        Paragraph("<b>MODEL PUBLIC SCHOOL</b>", styles['Heading1']),
        Paragraph("Affiliated to CBSE, New Delhi", styles['Heading3']),
        Paragraph("123 Education Street, Knowledge City - 560001", styles['Normal']),
        Paragraph("Phone: +91-80-12345678 | Email: info@modelpublicschool.edu.in", styles['Normal']),
        Paragraph("Website: www.modelpublicschool.edu.in", styles['Normal']),
        Spacer(1, 20)
    ]
    
    elements.extend(school_info)
    
    # Report Card Title
    elements.append(Paragraph(f"<b>REPORT CARD</b>", title_style))
    elements.append(Spacer(1, 20))
    
    # Student Information Table
    student = report_card.student
    student_data = [
        ["Student Name:", f"{student.user.get_full_name()}"],
        ["Admission No:", student.admission_number],
        ["Roll No:", student.roll_number],
        ["Class:", f"{report_card.class_name.name} - Section {report_card.class_name.section}"],
        ["Academic Year:", report_card.academic_year],
        ["Term:", report_card.get_term_display()],
        ["Father's Name:", student.father_name],
        ["Mother's Name:", student.mother_name],
    ]
    
    student_table = Table(student_data, colWidths=[2*inch, 3*inch])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(student_table)
    elements.append(Spacer(1, 30))
    
    # Academic Performance Header
    elements.append(Paragraph("<b>ACADEMIC PERFORMANCE</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    # Subject-wise Marks Table
    subject_data = report_card.get_subject_wise_marks()
    
    table_data = [["Subject", "Total Marks", "Marks Obtained", "Percentage", "Grade", "Grade Point"]]
    
    for subject, data in subject_data.items():
        table_data.append([
            subject.name,
            f"{data['total_marks']:.2f}",
            f"{data['obtained_marks']:.2f}",
            f"{data['percentage']:.2f}%",
            data['grades'][0] if data['grades'] else "-",
            f"{data['average_grade_point']:.2f}"
        ])
    
    marks_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch, 1*inch])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))
    
    elements.append(marks_table)
    elements.append(Spacer(1, 30))
    
    # Overall Summary
    summary_data = [
        ["Overall Total Marks:", f"{report_card.total_marks:.2f}"],
        ["Overall Marks Obtained:", f"{report_card.obtained_marks:.2f}"],
        ["Percentage:", f"{report_card.percentage:.2f}%"],
        ["Overall Grade:", report_card.overall_grade],
        ["Grade Point Average (GPA):", f"{report_card.grade_point_average:.2f}"],
        ["Class Rank:", f"{report_card.rank}" if report_card.rank else "Not Ranked"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Attendance Summary
    elements.append(Paragraph("<b>ATTENDANCE SUMMARY</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    attendance_data = [
        ["Total Working Days:", str(report_card.total_working_days)],
        ["Days Present:", str(report_card.days_present)],
        ["Days Absent:", str(report_card.total_working_days - report_card.days_present)],
        ["Attendance Percentage:", f"{report_card.attendance_percentage:.2f}%"],
    ]
    
    attendance_table = Table(attendance_data, colWidths=[2*inch, 2*inch])
    attendance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f8ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(attendance_table)
    elements.append(Spacer(1, 40))
    
    # Remarks Section
    if report_card.remarks or report_card.class_teacher_remarks or report_card.principal_remarks:
        elements.append(Paragraph("<b>REMARKS</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        if report_card.remarks:
            elements.append(Paragraph(f"<b>General Remarks:</b> {report_card.remarks}", styles['Normal']))
            elements.append(Spacer(1, 10))
        
        if report_card.class_teacher_remarks:
            elements.append(Paragraph(f"<b>Class Teacher's Remarks:</b> {report_card.class_teacher_remarks}", styles['Normal']))
            elements.append(Spacer(1, 10))
        
        if report_card.principal_remarks:
            elements.append(Paragraph(f"<b>Principal's Remarks:</b> {report_card.principal_remarks}", styles['Normal']))
    
    elements.append(Spacer(1, 40))
    
    # Signatures
    signature_data = [
        ["", "", ""],
        ["Class Teacher's Signature", "Principal's Signature", "Parent's Signature"],
        ["", "", ""],
        ["", "", ""],
        ["Date: _________________", "Date: _________________", "Date: _________________"],
    ]
    
    signature_table = Table(signature_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, 2), (0, 2), 1, colors.black),
        ('LINEABOVE', (1, 2), (1, 2), 1, colors.black),
        ('LINEABOVE', (2, 2), (2, 2), 1, colors.black),
    ]))
    
    elements.append(signature_table)
    
    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<i>Note: This is a computer generated report card and does not require signature.</i>", 
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))
    
    # Build PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

def generate_html_report_card(report_card):
    """Generate HTML version of report card"""
    template = get_template('reports/report_card_template.html')
    context = {
        'report_card': report_card,
        'student': report_card.student,
        'subject_data': report_card.get_subject_wise_marks(),
        'current_date': datetime.datetime.now().strftime('%d-%m-%Y'),
    }
    html = template.render(context)
    return html

def generate_bulk_report_cards(class_id, term, academic_year):
    """Generate report cards for all students in a class"""
    from students.models import Student
    from grades.models import ReportCard
    
    students = Student.objects.filter(class_enrolled_id=class_id, is_active=True)
    report_cards = []
    
    for student in students:
        # Create or get report card
        report_card, created = ReportCard.objects.get_or_create(
            student=student,
            academic_year=academic_year,
            term=term,
            class_name=student.class_enrolled
        )
        
        # Calculate performance
        report_card.calculate_performance()
        
        # Calculate rank
        calculate_ranks(class_id, term, academic_year)
        
        report_cards.append(report_card)
    
    return report_cards

def calculate_ranks(class_id, term, academic_year):
    """Calculate ranks for all students in a class"""
    from grades.models import ReportCard
    
    report_cards = ReportCard.objects.filter(
        class_name_id=class_id,
        term=term,
        academic_year=academic_year
    ).order_by('-percentage')
    
    rank = 1
    for report_card in report_cards:
        report_card.rank = rank
        report_card.save()
        rank += 1