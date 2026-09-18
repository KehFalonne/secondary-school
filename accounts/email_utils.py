from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import AccessRequest, User


def send_approval_email(access_request: AccessRequest, user: User):
    """Send approval email to the user with login credentials"""
    subject = 'Your School System Account Has Been Approved'
    
    context = {
        'first_name': access_request.first_name,
        'last_name': access_request.last_name,
        'user_type': access_request.get_user_type_display(),
        'username': user.username,
        'email': user.email,
        'approved_by': access_request.approved_by.get_full_name(),
        'school_name': 'School System',
        'login_url': 'http://127.0.0.1:8000/accounts/login/',
    }
    
    # Try to render from template if it exists, fallback to basic email
    try:
        html_message = render_to_string('accounts/emails/approval_email.html', context)
        plain_message = strip_tags(html_message)
    except:
        plain_message = f"""
Dear {access_request.first_name} {access_request.last_name},

Your access request to the School System has been APPROVED!

Your account details:
- Username: {user.username}
- Email: {user.email}
- User Type: {access_request.get_user_type_display()}
- Approved by: {access_request.approved_by.get_full_name()}

You can now log in using your username and the temporary password that was sent to you separately.

Please change your password after your first login for security purposes.

Login URL: http://127.0.0.1:8000/accounts/login/

Best regards,
School System Administration
        """
        html_message = None
    
    try:
        if html_message:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[access_request.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
        else:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[access_request.email],
                fail_silently=False,
            )
        
        # Mark email as sent
        access_request.approval_email_sent = True
        access_request.approval_email_sent_at = timezone.now()
        access_request.save(update_fields=['approval_email_sent', 'approval_email_sent_at'])
        
        return True, "Approval email sent successfully"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"


def send_rejection_email(access_request: AccessRequest):
    """Send rejection email to the user"""
    subject = 'Your School System Access Request Status'
    
    context = {
        'first_name': access_request.first_name,
        'last_name': access_request.last_name,
        'rejection_reason': access_request.rejection_reason or 'Not specified',
        'school_name': 'School System',
    }
    
    try:
        html_message = render_to_string('accounts/emails/rejection_email.html', context)
        plain_message = strip_tags(html_message)
    except:
        plain_message = f"""
Dear {access_request.first_name} {access_request.last_name},

Thank you for your interest in accessing the School System.

Unfortunately, your access request has been REJECTED.

Reason: {access_request.rejection_reason or 'Not specified'}

If you believe this is a mistake, please contact the school administration for more information.

Best regards,
School System Administration
        """
        html_message = None
    
    try:
        if html_message:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[access_request.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
        else:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[access_request.email],
                fail_silently=False,
            )
        
        # Mark email as sent
        access_request.rejection_email_sent = True
        access_request.rejection_email_sent_at = timezone.now()
        access_request.save(update_fields=['rejection_email_sent', 'rejection_email_sent_at'])
        
        return True, "Rejection email sent successfully"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"


def send_credential_email(user: User, temp_password: str):
    """Send credentials email with temporary password"""
    subject = 'Your School System Login Credentials'
    
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'email': user.email,
        'temp_password': temp_password,
        'school_name': 'School System',
        'login_url': 'http://127.0.0.1:8000/accounts/login/',
    }
    
    try:
        html_message = render_to_string('accounts/emails/credentials_email.html', context)
        plain_message = strip_tags(html_message)
    except:
        plain_message = f"""
Dear {user.first_name} {user.last_name},

Welcome to the School System! Here are your login credentials:

Username: {user.username}
Email: {user.email}
Temporary Password: {temp_password}

Please keep these credentials safe and do not share them with anyone.

We strongly recommend changing your password after your first login.

Login URL: http://127.0.0.1:8000/accounts/login/

Best regards,
School System Administration
        """
        html_message = None
    
    try:
        if html_message:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
        else:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        
        return True, "Credentials email sent successfully"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"
