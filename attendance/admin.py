from django.contrib import admin
from .models import Student, Attendance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'classroom', 'avatar_emoji', 'is_active', 'date_created')
    list_filter = ('classroom', 'is_active')
    search_fields = ('first_name', 'last_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'mood', 'checked_in_at', 'checked_in_by')
    list_filter = ('status', 'date', 'mood', 'student__classroom')
    search_fields = ('student__first_name', 'student__last_name')

