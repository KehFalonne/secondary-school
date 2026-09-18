from django.test import TestCase

from .forms import AccessRequestForm
from .models import AccessRequest, User


class UserModelTests(TestCase):
    def test_user_string_includes_full_name_and_username(self):
        user = User.objects.create_user(
            username='jdoe', 
            password='Strong-password-123',
            first_name='Jane',
            last_name='Doe',
        )

        self.assertEqual(str(user), 'Jane Doe (jdoe)')
        self.assertTrue(user.check_password('Strong-password-123'))


class AccessRequestFormTests(TestCase):
    def test_email_cannot_be_requested_by_an_existing_user(self):
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='Strong-password-123',
        )

        form = AccessRequestForm(
            data={
                'email': 'existing@example.com',
                'user_type': 'student',
                'first_name': 'New',
                'last_name': 'User',
                'phone': '',
                'reason': 'I need access for enrollment.',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('already exists', form.errors['email'][0])

    def test_email_cannot_have_two_pending_requests(self):
        AccessRequest.objects.create(
            email='pending@example.com',
            user_type='student',
            first_name='Pending',
            last_name='User',
            reason='I need access for enrollment.',
        )

        form = AccessRequestForm(
            data={
                'email': 'pending@example.com',
                'user_type': 'student',
                'first_name': 'Another',
                'last_name': 'User',
                'phone': '',
                'reason': 'I need access too.',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('already submitted', form.errors['email'][0])
