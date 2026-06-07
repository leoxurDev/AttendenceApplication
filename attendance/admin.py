from django.contrib import admin
from .models import Student, Attendance, ClassroomOption, AvatarEmoji, AvatarColor, AssignmentGroup, SupportEngineer, SupportTicket, TicketActivity, TeacherSupportPermission


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


@admin.register(TeacherSupportPermission)
class TeacherSupportPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_raise_tickets')
    list_filter = ('can_raise_tickets',)
    search_fields = ('user__username',)


@admin.register(AssignmentGroup)
class AssignmentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(SupportEngineer)
class SupportEngineerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'email')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('number', 'caller', 'subject', 'state', 'priority', 'created_at')
    list_filter = ('state', 'priority', 'created_at')
    search_fields = ('number', 'caller', 'subject')


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'activity_type', 'author', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('ticket__number', 'author', 'content')



