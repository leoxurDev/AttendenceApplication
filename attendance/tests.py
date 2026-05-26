import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Student, ClassroomOption, AvatarEmoji, AvatarColor, AppLayoutBlock

class StudentPINCodeTests(TestCase):
    def setUp(self):
        # Create supporting records
        self.classroom = ClassroomOption.objects.create(emoji="🐝", name="Bumblebees", order=1)
        self.emoji = AvatarEmoji.objects.create(emoji="🦁", name="Lion", order=1)
        self.color = AvatarColor.objects.create(hex_code="#FDFFB6", name="Pastel Yellow", order=1)
        
        self.student = Student.objects.create(
            first_name="Leo",
            last_name="Lion",
            classroom="Bumblebees",
            avatar_emoji="🦁",
            avatar_color="#FDFFB6",
            pin_code="1234"
        )

    def test_valid_pin_code(self):
        # The default pin 1234 is valid
        self.student.full_clean()
        
        # Change PIN to another valid 4 digit string
        self.student.pin_code = "9876"
        self.student.full_clean()  # Should not raise ValidationError

    def test_invalid_pin_code_length(self):
        # 3 digits PIN
        self.student.pin_code = "123"
        with self.assertRaises(ValidationError):
            self.student.full_clean()

        # 5 digits PIN
        self.student.pin_code = "12345"
        with self.assertRaises(ValidationError):
            self.student.full_clean()

    def test_invalid_pin_code_chars(self):
        # PIN containing non-digits
        self.student.pin_code = "abcd"
        with self.assertRaises(ValidationError):
            self.student.full_clean()

        self.student.pin_code = "12a4"
        with self.assertRaises(ValidationError):
            self.student.full_clean()


class StudentPINVerifyAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = Student.objects.create(
            first_name="Leo",
            last_name="Lion",
            classroom="Bumblebees",
            avatar_emoji="🦁",
            avatar_color="#FDFFB6",
            pin_code="1234"
        )

    def test_verify_pin_success(self):
        url = reverse('verify_pin')
        response = self.client.post(url, {
            'student_id': self.student.id,
            'pin_code': '1234'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_verify_pin_failure(self):
        url = reverse('verify_pin')
        response = self.client.post(url, {
            'student_id': self.student.id,
            'pin_code': '1111'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_verify_pin_non_existent_student(self):
        url = reverse('verify_pin')
        response = self.client.post(url, {
            'student_id': 99999,
            'pin_code': '1234'
        })
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])


class TeacherAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = User.objects.create_user(
            username='teacher_test',
            email='test@school.com',
            password='testpassword123'
        )
        self.classroom = ClassroomOption.objects.create(emoji="🐝", name="Bumblebees", order=1)
        self.student = Student.objects.create(
            first_name="Toby",
            last_name="Tiger",
            classroom="Bumblebees",
            avatar_emoji="🐯",
            avatar_color="#FFD6A5",
            pin_code="1002"
        )

    def test_unauthenticated_redirect(self):
        # Accessing dashboard directly should redirect to login
        url = reverse('teacher_dashboard')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('teacher_login') + f"?next={url}")

    def test_teacher_login_success(self):
        url = reverse('teacher_login')
        response = self.client.post(url, {
            'username': 'teacher_test',
            'password': 'testpassword123'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))
        
        # Verify the session is now authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_teacher_login_failure(self):
        url = reverse('teacher_login')
        response = self.client.post(url, {
            'username': 'teacher_test',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_teacher_registration(self):
        url = reverse('teacher_register')
        response = self.client.post(url, {
            'username': 'new_teacher',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'  # Note: Django's default UserCreationForm uses password1 and password2
        })
        # Wait, UserCreationForm uses password1 and password2! Let's check:
        # Django's standard UserCreationForm has: username, password1, password2.
        # Let's verify by testing if password1 and password2 are correct.
        response = self.client.post(url, {
            'username': 'new_teacher',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))
        self.assertTrue(User.objects.filter(username='new_teacher').exists())

    def test_teacher_logout(self):
        # Log in first
        self.client.login(username='teacher_test', password='testpassword123')
        self.assertTrue(self.client.session.keys())
        
        # Log out
        url = reverse('teacher_logout')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('student_grid'))
        
        # Verify logged out
        # We can try to access the dashboard now
        dashboard_url = reverse('teacher_dashboard')
        dashboard_response = self.client.get(dashboard_url)
        self.assertRedirects(dashboard_response, reverse('teacher_login') + f"?next={dashboard_url}")

    def test_unified_login_context(self):
        url = reverse('unified_login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.context)
        self.assertIn('classrooms', response.context)


class DeveloperCustomizerTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Normal staff user
        self.staff_user = User.objects.create_user(
            username='admin_test',
            email='admin@school.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )
        # Regular teacher user (non-staff)
        self.regular_user = User.objects.create_user(
            username='teacher_non_admin',
            email='teacher@school.com',
            password='password123'
        )

    def test_developer_page_unauthenticated_redirect(self):
        url = reverse('admin_developer_page')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('teacher_login') + f"?next={url}")

    def test_developer_page_non_staff_denied(self):
        self.client.login(username='teacher_non_admin', password='password123')
        url = reverse('admin_developer_page')
        response = self.client.get(url)
        # Standard redirect back to dashboard on messages error
        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_developer_page_staff_success(self):
        self.client.login(username='admin_test', password='adminpassword123')
        url = reverse('admin_developer_page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('layout_blocks', response.context)
        # Should have seeded 4 blocks
        self.assertEqual(len(response.context['layout_blocks']), 4)

    def test_save_layout_api(self):
        self.client.login(username='admin_test', password='adminpassword123')
        # Seed blocks first by loading page
        self.client.get(reverse('admin_developer_page'))
        
        # Post new layout
        url = reverse('save_layout')
        payload = {
            'blocks': [
                {'id': 'stats_banner', 'order': 1, 'is_visible': False},
                {'id': 'header', 'order': 2, 'is_visible': True},
                {'id': 'classroom_tabs', 'order': 3, 'is_visible': True},
                {'id': 'student_grid', 'order': 4, 'is_visible': True}
            ]
        }
        response = self.client.post(
            url, 
            data=json.dumps(payload), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify database
        block = AppLayoutBlock.objects.get(block_id='stats_banner')
        self.assertEqual(block.order, 1)
        self.assertFalse(block.is_visible)

    def test_ai_chat_command_fallback(self):
        self.client.login(username='admin_test', password='adminpassword123')
        # Seed blocks first
        self.client.get(reverse('admin_developer_page'))
        
        url = reverse('ai_chat_command')
        payload = {
            'message': 'hide stats banner',
            'api_key': '' # No API key, forces fallback offline parsing
        }
        response = self.client.post(
            url, 
            data=json.dumps(payload), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json['success'])
        self.assertEqual(res_json['action'], 'hide')
        self.assertEqual(res_json['block'], 'stats_banner')
        
        # Verify stats banner hidden in DB
        self.assertFalse(AppLayoutBlock.objects.get(block_id='stats_banner').is_visible)


