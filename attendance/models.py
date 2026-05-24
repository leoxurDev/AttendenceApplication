from django.db import models
from django.utils import timezone

class Student(models.Model):
    CLASSROOM_CHOICES = [
        ('Bumblebees', 'Bumblebees 🐝'),
        ('Butterflies', 'Butterflies 🦋'),
        ('Ladybugs', 'Ladybugs 🐞'),
    ]

    AVATAR_EMOJIS = [
        ('🦁', 'Lion 🦁'),
        ('🐯', 'Tiger 🐯'),
        ('🐘', 'Elephant 🐘'),
        ('🐼', 'Panda 🐼'),
        ('🦊', 'Fox 🦊'),
        ('🐨', 'Koala 🐨'),
        ('🦖', 'Dino 🦖'),
        ('🦄', 'Unicorn 🦄'),
        ('🐰', 'Bunny 🐰'),
        ('🐸', 'Frog 🐸'),
        ('🦉', 'Owl 🦉'),
        ('🐝', 'Bee 🐝'),
        ('🦋', 'Butterfly 🦋'),
        ('🐳', 'Whale 🐳'),
        ('🦀', 'Crab 🦀'),
        ('🐬', 'Dophin 🐬'),
    ]

    AVATAR_COLORS = [
        ('#FFADAD', 'Pastel Red'),
        ('#FFD6A5', 'Pastel Orange'),
        ('#FDFFB6', 'Pastel Yellow'),
        ('#CAFFBF', 'Pastel Green'),
        ('#9BF6FF', 'Pastel Cyan'),
        ('#A0C4FF', 'Pastel Blue'),
        ('#BDB2FF', 'Pastel Purple'),
        ('#FFC6FF', 'Pastel Pink'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    classroom = models.CharField(max_length=20, choices=CLASSROOM_CHOICES, default='Bumblebees')
    avatar_emoji = models.CharField(max_length=5, choices=AVATAR_EMOJIS, default='🦁')
    avatar_color = models.CharField(max_length=7, choices=AVATAR_COLORS, default='#A0C4FF')
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
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.CharField(max_length=15, default='child')

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date', 'student__first_name']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.status})"

