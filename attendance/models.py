from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class ClassroomOption(models.Model):
    emoji = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Classroom Options'

    def __str__(self):
        return f"{self.emoji} {self.name}"

    @property
    def display_value(self):
        return f"{self.emoji} {self.name}"


class AvatarEmoji(models.Model):
    emoji = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Avatar Emoji'
        verbose_name_plural = 'Avatar Emojis'

    def __str__(self):
        return f"{self.emoji} {self.name}"


class AvatarColor(models.Model):
    hex_code = models.CharField(max_length=7, unique=True)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Avatar Colors'

    def __str__(self):
        return f"{self.name} ({self.hex_code})"

    @property
    def display_value(self):
        return self.hex_code


class Student(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    classroom = models.CharField(max_length=50)
    avatar_emoji = models.CharField(max_length=5)
    avatar_color = models.CharField(max_length=7)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    pin_code = models.CharField(
        max_length=4,
        default="1234",
        validators=[RegexValidator(r'^\d{4}$', 'PIN code must be exactly 4 digits.')]
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.classroom})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def today_attendance(self):
        today = timezone.localdate()
        return self.attendance_set.filter(date=today).first()


class Attendance(models.Model):
    TIME_PERIOD_CHOICES = [
        ('morning', 'Morning (5 AM - 12 PM)'),
        ('afternoon', 'Afternoon (12 PM - 5 PM)'),
        ('evening', 'Evening (5 PM - 11:59 PM)'),
    ]

    STATUS_CHOICES = [
        ('present', 'Present ☀️'),
        ('absent', 'Absent 🌙'),
        ('late', 'Late ⏰'),
    ]

    MOOD_CHOICES = [
        ('happy', 'Happy 😊'),
        ('excited', 'Excited 🤩'),
        ('sleepy', 'Sleepy 🥱'),
        ('silly', 'Silly 🤪'),
        ('sad', 'Sad 😢'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES, blank=True, null=True)
    time_period = models.CharField(max_length=10, choices=TIME_PERIOD_CHOICES, blank=True, null=True)
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.CharField(max_length=15, default='child')

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date', 'student__first_name']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.status})"

    @staticmethod
    def get_current_time_period():
        """Determine the current time period based on system time."""
        hour = timezone.localtime().hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        else:
            return 'evening'

    def save(self, *args, **kwargs):
        """Auto-set time_period if not already set."""
        if not self.time_period:
            self.time_period = self.get_current_time_period()
        super().save(*args, **kwargs)

    @classmethod
    def get_moods_for_time_period(cls, time_period):
        """Get mood choices appropriate for a specific time period."""
        return [mood for mood in cls.MOOD_CHOICES]


class AppLayoutBlock(models.Model):
    block_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} (order: {self.order}, visible: {self.is_visible})"


class AssignmentGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SupportEngineer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=128, default="engineer123")
    groups = models.ManyToManyField(AssignmentGroup, blank=True, related_name='engineers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        grps = ", ".join([g.name for g in self.groups.all()])
        if grps:
            return f"{self.name} ({grps})"
        return self.name


class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATE_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    number = models.CharField(max_length=15, unique=True, blank=True)
    caller = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='moderate')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='new')
    assignment_group = models.ForeignKey(AssignmentGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    assigned_to = models.ForeignKey(SupportEngineer, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.number} - {self.subject} ({self.state})"

    def save(self, *args, **kwargs):
        if self.state in ['resolved', 'closed']:
            if not self.resolved_at:
                self.resolved_at = timezone.now()
        else:
            self.resolved_at = None

        if not self.number:
            super().save(*args, **kwargs)
            self.number = f"TKT{100000 + self.id}"
            SupportTicket.objects.filter(pk=self.id).update(number=self.number)
        else:
            super().save(*args, **kwargs)

    def _format_timedelta(self, td):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def get_sla_status(self):
        durations = {
            'critical': timedelta(hours=1),
            'high': timedelta(hours=4),
            'moderate': timedelta(hours=8),
            'low': timedelta(hours=24),
        }
        sla_duration = durations.get(self.priority, timedelta(hours=8))
        deadline = self.created_at + sla_duration
        
        # If resolved or closed, check if resolved before deadline
        if self.state in ['resolved', 'closed']:
            end_time = self.resolved_at or self.updated_at
            if end_time <= deadline:
                return {
                    'status': 'met',
                    'label': 'SLA: Met',
                    'class': 'badge-moderate'
                }
            else:
                overdue = end_time - deadline
                overdue_str = self._format_timedelta(overdue)
                return {
                    'status': 'breached_resolved',
                    'label': f'SLA: Breached (by {overdue_str})',
                    'class': 'badge-critical'
                }
        
        # If active, calculate remaining time
        now = timezone.now()
        if now > deadline:
            overdue = now - deadline
            overdue_str = self._format_timedelta(overdue)
            return {
                'status': 'breached',
                'label': f'SLA: Breached (by {overdue_str})',
                'class': 'badge-critical'
            }
        else:
            remaining = deadline - now
            remaining_str = self._format_timedelta(remaining)
            if remaining < (sla_duration / 4):
                return {
                    'status': 'warning',
                    'label': f'SLA: Warning ({remaining_str} left)',
                    'class': 'badge-high'
                }
            return {
                'status': 'active',
                'label': f'SLA: Active ({remaining_str} left)',
                'class': 'badge-state-new'
            }


class TicketActivity(models.Model):
    TYPE_CHOICES = [
        ('work_note', 'Work Note (Internal)'),
        ('customer_comment', 'Customer Comment (Visible to Client)'),
    ]

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    author = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()} by {self.author} at {self.created_at}"


class TeacherSupportPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='support_permission')
    can_raise_tickets = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Can raise support: {self.can_raise_tickets}"


