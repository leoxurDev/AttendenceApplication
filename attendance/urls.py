from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('grid/', views.student_grid, name='student_grid'),
    path('toggle-attendance/', views.toggle_attendance, name='toggle_attendance'),
    path('verify-pin/', views.verify_pin, name='verify_pin'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('login/', views.teacher_login, name='unified_login'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher/add/', views.add_student, name='add_student'),
    path('teacher/edit/<int:pk>/', views.edit_student, name='edit_student'),
    path('teacher/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('teacher/export/', views.export_student_csv, name='export_student_csv'),
    path('teacher/developer/', views.admin_developer_page, name='admin_developer_page'),
    path('teacher/developer/save/', views.save_layout, name='save_layout'),
    path('teacher/developer/chat/', views.ai_chat_command, name='ai_chat_command'),
]
