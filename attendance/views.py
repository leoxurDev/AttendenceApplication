from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import csv
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from .models import Student, Attendance, ClassroomOption
from .forms import StudentForm

def student_grid(request):
    selected_classroom_name = request.GET.get('classroom')
    
    # Get all active classrooms
    all_classrooms = ClassroomOption.objects.filter(is_active=True).order_by('order')
    
    # Default to first classroom if not provided
    if not selected_classroom_name:
        selected_classroom = all_classrooms.first()
        if not selected_classroom:
            return render(request, 'attendance/student_grid.html', {'error': 'No active classrooms found'})
        selected_classroom_name = selected_classroom.name
        selected_classroom_display = selected_classroom.display_value
    else:
        try:
            selected_classroom = all_classrooms.get(name=selected_classroom_name)
            selected_classroom_display = selected_classroom.display_value
        except ClassroomOption.DoesNotExist:
            selected_classroom = all_classrooms.first()
            if not selected_classroom:
                return render(request, 'attendance/student_grid.html', {'error': 'No active classrooms found'})
            selected_classroom_name = selected_classroom.name
            selected_classroom_display = selected_classroom.display_value
        
    students = Student.objects.filter(classroom=selected_classroom_name, is_active=True).order_by('first_name')
    today = timezone.localdate()
    
    # Prefetch today's attendance records to avoid N+1 queries
    today_attendances = {
        att.student_id: att 
        for att in Attendance.objects.filter(date=today, student__classroom=selected_classroom_name)
    }
    
    # Attach attendance record to student objects
    for student in students:
        student.today_status = today_attendances.get(student.id)

    total_students = students.count()
    present_today = sum(1 for s in students if s.today_status and s.today_status.status in ['present', 'late'])
    attendance_rate = int((present_today / total_students * 100)) if total_students > 0 else 0
    
    classrooms_display = [(c.name, c.display_value) for c in all_classrooms]
    mood_choices = Attendance.MOOD_CHOICES
    current_time_period = Attendance.get_current_time_period()

    context = {
        'students': students,
        'selected_classroom': selected_classroom_display,
        'selected_classroom_name': selected_classroom_name,
        'classrooms': classrooms_display,
        'total_students': total_students,
        'present_today': present_today,
        'attendance_rate': attendance_rate,
        'mood_choices': mood_choices,
        'today': today,
        'current_time_period': current_time_period,
    }
    return render(request, 'attendance/student_grid.html', context)

@require_POST
def toggle_attendance(request):
    student_id = request.POST.get('student_id')
    status = request.POST.get('status', 'present')
    mood = request.POST.get('mood', None)
    checked_by = request.POST.get('checked_by', 'child')
    
    try:
        student = Student.objects.get(id=student_id, is_active=True)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
        
    today = timezone.localdate()
    attendance, created = Attendance.objects.get_or_create(
        student=student, 
        date=today,
        defaults={'status': status, 'mood': mood, 'checked_in_by': checked_by}
    )
    
    if not created:
        # If it already exists, let's toggle the status or update it
        if attendance.status == status and checked_by == 'child' and not mood:
            # If a kid double clicks their present card, reset it to absent (delete the record)
            attendance.delete()
            return JsonResponse({
                'success': True,
                'status': 'absent',
                'action': 'removed',
                'student_id': student_id
            })
        else:
            # Update status, mood and checked_by
            attendance.status = status
            if mood:
                attendance.mood = mood
            attendance.checked_in_by = checked_by
            attendance.save()
            
    time_str = timezone.localtime(attendance.checked_in_at).strftime('%I:%M %p')
    return JsonResponse({
        'success': True,
        'status': attendance.status,
        'mood': attendance.mood,
        'mood_emoji': attendance.get_mood_display().split()[-1] if attendance.mood else '',
        'time': time_str,
        'action': 'created' if created else 'updated',
        'student_id': student_id
    })

def teacher_dashboard(request):
    today = timezone.localdate()
    classroom_filter = request.GET.get('classroom', 'All')
    
    # Calculate metrics
    students_query = Student.objects.filter(is_active=True)
    attendance_query = Attendance.objects.filter(date=today)
    
    if classroom_filter != 'All':
        students_query = students_query.filter(classroom=classroom_filter)
        attendance_query = attendance_query.filter(student__classroom=classroom_filter)
        
    students = students_query.order_by('classroom', 'first_name')
    total_students = students.count()
    
    # Map attendance details for easy checking
    attendance_map = {att.student_id: att for att in attendance_query}
    
    present_count = 0
    late_count = 0
    absent_count = 0
    
    for student in students:
        att = attendance_map.get(student.id)
        student.today_status = att
        if att:
            if att.status == 'present':
                present_count += 1
            elif att.status == 'late':
                late_count += 1
            else:
                absent_count += 1
        else:
            absent_count += 1

    attendance_percentage = int(( (present_count + late_count) / total_students * 100)) if total_students > 0 else 0

    active_classrooms = ClassroomOption.objects.filter(is_active=True).order_by('order')
    classrooms = [('All', 'All Classes 🏫')] + [(c.name, c.display_value) for c in active_classrooms]

    context = {
        'students': students,
        'today': today,
        'total_students': total_students,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'classrooms': classrooms,
        'selected_classroom': classroom_filter,
    }
    return render(request, 'attendance/teacher_dashboard.html', context)

def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Welcome to the school, {student.full_name}! 🎉")
            return redirect('teacher_dashboard')
    else:
        form = StudentForm()
        
    return render(request, 'attendance/student_form.html', {'form': form, 'title': 'Add New Student 🐣'})

def edit_student(request, pk):
    student = get_object_or_404(Student, id=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated details for {student.full_name}! 📝")
            return redirect('teacher_dashboard')
    else:
        form = StudentForm(instance=student)
        
    return render(request, 'attendance/student_form.html', {'form': form, 'title': f'Edit Details for {student.first_name} ✏️'})

def delete_student(request, pk):
    student = get_object_or_404(Student, id=pk)
    if request.method == 'POST':
        student.is_active = False  # Soft delete
        student.save()
        messages.warning(request, f"Goodbye {student.full_name}! 👋")
        return redirect('teacher_dashboard')
    return render(request, 'attendance/student_confirm_delete.html', {'student': student})


def export_student_csv(request):
    classroom_filter = request.GET.get('classroom', 'All')
    
    # Filter active students based on classroom
    students = Student.objects.filter(is_active=True)
    if classroom_filter != 'All':
        students = students.filter(classroom=classroom_filter)
        
    students = students.order_by('classroom', 'first_name')
    today = timezone.localdate()
    
    # Today's attendance pre-fetch
    today_attendances = {
        att.student_id: att 
        for att in Attendance.objects.filter(date=today)
    }
    
    response = HttpResponse(content_type='text/csv')
    filename = f"kindergarten_attendance_{classroom_filter}_{today}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'First Name', 'Last Name', 'Classroom', 
        'Avatar Emoji', 'Today Status', 'Today Mood', 'Time Period', 'Today Check-in Time'
    ])
    
    for s in students:
        att = today_attendances.get(s.id)
        status = att.status if att else 'absent'
        mood = att.get_mood_display() if (att and att.mood) else '-'
        time_period = att.get_time_period_display() if (att and att.time_period) else '-'
        
        if att and att.status != 'absent':
            checkin_time = timezone.localtime(att.checked_in_at).strftime('%I:%M %p')
        else:
            checkin_time = '-'
            
        writer.writerow([
            s.id, s.first_name, s.last_name, s.classroom,
            s.avatar_emoji, status.capitalize(), mood, time_period, checkin_time
        ])
        
    return response

