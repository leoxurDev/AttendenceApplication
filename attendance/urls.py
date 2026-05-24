from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_grid, name='student_grid'),
    path('toggle-attendance/', views.toggle_attendance, name='toggle_attendance'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/add/', views.add_student, name='add_student'),
    path('teacher/edit/<int:pk>/', views.edit_student, name='edit_student'),
    path('teacher/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('teacher/export/', views.export_student_csv, name='export_student_csv'),
]
