from django.contrib import admin
from .models import Student, Attendance, ClassroomOption, AvatarEmoji, AvatarColor


@admin.register(ClassroomOption)
class ClassroomOptionAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'name', 'description', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'emoji')


@admin.register(AvatarEmoji)
class AvatarEmojiAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'emoji')


@admin.register(AvatarColor)
class AvatarColorAdmin(admin.ModelAdmin):
    list_display = ('hex_code', 'name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'hex_code')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'classroom', 'avatar_emoji', 'is_active', 'date_created')
    list_filter = ('classroom', 'is_active')
    search_fields = ('first_name', 'last_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'mood', 'time_period', 'checked_in_at', 'checked_in_by')
    list_filter = ('status', 'date', 'mood', 'time_period', 'student__classroom')
    search_fields = ('student__first_name', 'student__last_name')


