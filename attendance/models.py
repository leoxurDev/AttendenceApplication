from django.db import models
from django.utils import timezone


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

