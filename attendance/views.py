from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import csv
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Student, Attendance, ClassroomOption, AppLayoutBlock, AssignmentGroup, SupportEngineer, SupportTicket, TicketActivity, TeacherSupportPermission
from .forms import StudentForm

def get_or_seed_layout_blocks():
    blocks = AppLayoutBlock.objects.all().order_by('order')
    if not blocks.exists():
        default_blocks = [
            ('header', 'Branding Header', 1),
            ('classroom_tabs', 'Classroom Selection Tabs', 2),
            ('stats_banner', 'Roster Stats Banner', 3),
            ('student_grid', 'Student Roster Grid', 4)
        ]
        for bid, name, o in default_blocks:
            AppLayoutBlock.objects.create(block_id=bid, title=name, order=o, is_visible=True)
        blocks = AppLayoutBlock.objects.all().order_by('order')
    return blocks

def get_school_schedule_status():
    import datetime
    local_now = timezone.localtime()
    current_time = local_now.time()
    
    # Parse times
    start_time = datetime.time(9, 30)
    recess1_start = datetime.time(11, 0)
    recess1_end = datetime.time(11, 15)
    lunch_start = datetime.time(12, 0)
    lunch_end = datetime.time(13, 0)
    recess2_start = datetime.time(14, 0)
    recess2_end = datetime.time(14, 15)
    end_time = datetime.time(15, 30)
    
    if current_time < start_time:
        status = "Before School 🌅"
        message = "Check-in active. School starts at 9:30 AM."
        badge = "active"
    elif recess1_start <= current_time < recess1_end:
        status = "Morning Recess 🧸"
        message = "Morning playtime interval in progress."
        badge = "recess"
    elif lunch_start <= current_time < lunch_end:
        status = "Lunch Hour 🍔"
        message = "Lunch break (12:00 PM - 1:00 PM)."
        badge = "lunch"
    elif recess2_start <= current_time < recess2_end:
        status = "Afternoon Recess 🧃"
        message = "Afternoon play interval in progress."
        badge = "recess"
    elif start_time <= current_time < end_time:
        status = "Class Time 📚"
        message = "Learning and activities in progress."
        badge = "class"
    else:
        status = "School Closed 🌙"
        message = "School day ended at 3:30 PM. See you tomorrow!"
        badge = "closed"
        
    milestones = [
        {'time_str': '09:30 AM', 'time': start_time, 'label': 'Starts 🎒'},
        {'time_str': '11:00 AM', 'time': recess1_start, 'label': 'Recess 🧸'},
        {'time_str': '12:00 PM', 'time': lunch_start, 'label': 'Lunch 🍔'},
        {'time_str': '02:00 PM', 'time': recess2_start, 'label': 'Recess 🧃'},
        {'time_str': '03:30 PM', 'time': end_time, 'label': 'End 🚪'},
    ]
    
    # Calculate status class for each milestone
    active_idx = -1
    for idx, m in enumerate(milestones):
        if current_time >= m['time']:
            active_idx = idx
            
    for idx, m in enumerate(milestones):
        if current_time >= end_time:
            m['status_class'] = 'completed'
        elif idx < active_idx:
            m['status_class'] = 'completed'
        elif idx == active_idx:
            m['status_class'] = 'active'
        else:
            m['status_class'] = 'upcoming'
            
    return {
        'status': status,
        'message': message,
        'badge': badge,
        'current_time_str': local_now.strftime('%I:%M %p'),
        'milestones': milestones,
    }

def home(request):
    return render(request, 'attendance/home.html')

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
        'layout_blocks': get_or_seed_layout_blocks(),
        'schedule_status': get_school_schedule_status(),
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
        
    # Auto-late classification for child check-in
    if checked_by == 'child' and status == 'present':
        import datetime
        local_now = timezone.localtime()
        if local_now.time() >= datetime.time(9, 30):
            status = 'late'
        
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

@require_POST
def verify_pin(request):
    student_id = request.POST.get('student_id')
    pin_code = request.POST.get('pin_code')
    try:
        student = Student.objects.get(id=student_id, is_active=True)
        if student.pin_code == pin_code:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid PIN. Please try again! 🤫'})
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found.'}, status=404)

def teacher_login(request):
    if request.user.is_authenticated:
        return redirect('teacher_dashboard')
        
    students = Student.objects.filter(is_active=True).order_by('classroom', 'first_name')
    classrooms = ClassroomOption.objects.filter(is_active=True).order_by('order')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, Teacher {user.username}! 🍎")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()
        
    context = {
        'form': form,
        'action': 'login',
        'students': students,
        'classrooms': classrooms,
        'schedule_status': get_school_schedule_status(),
    }
    return render(request, 'attendance/login.html', context)

def teacher_register(request):
    if request.user.is_authenticated:
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Registration successful! Welcome, Teacher {user.username}! 🏫")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'attendance/login.html', {'form': form, 'action': 'register'})

def teacher_logout(request):
    auth_logout(request)
    messages.info(request, "You have been logged out. See you soon! 👋")
    return redirect('student_grid')

@login_required(login_url='teacher_login')
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

    # Check if this teacher can raise tickets
    can_raise_support = False
    tickets_list = []
    if request.user.is_authenticated:
        can_raise_support = request.user.is_superuser
        if not can_raise_support:
            from .models import TeacherSupportPermission
            perm, created = TeacherSupportPermission.objects.get_or_create(user=request.user)
            can_raise_support = perm.can_raise_tickets
            
        if can_raise_support:
            tickets_list = SupportTicket.objects.all().order_by('-created_at')

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
        'schedule_status': get_school_schedule_status(),
        'current_time_period': Attendance.get_current_time_period(),
        'can_raise_support': can_raise_support,
        'tickets_list': tickets_list,
    }
    return render(request, 'attendance/teacher_dashboard.html', context)

@login_required(login_url='teacher_login')
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

@login_required(login_url='teacher_login')
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

@login_required(login_url='teacher_login')
def delete_student(request, pk):
    student = get_object_or_404(Student, id=pk)
    if request.method == 'POST':
        student.is_active = False  # Soft delete
        student.save()
        messages.warning(request, f"Goodbye {student.full_name}! 👋")
        return redirect('teacher_dashboard')
    return render(request, 'attendance/student_confirm_delete.html', {'student': student})


@login_required(login_url='teacher_login')
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


@login_required(login_url='teacher_login')
@ensure_csrf_cookie
def admin_developer_page(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied. Only administrators can use the customizer page. 🔐")
        return redirect('teacher_dashboard')
        
    # Handle permission toggle POST form
    if request.method == 'POST' and 'toggle_support_user_id' in request.POST:
        user_id = request.POST.get('toggle_support_user_id')
        user_to_toggle = get_object_or_404(User, pk=user_id)
        perm, created = TeacherSupportPermission.objects.get_or_create(user=user_to_toggle)
        perm.can_raise_tickets = not perm.can_raise_tickets
        perm.save()
        messages.success(request, f"Updated support ticket permissions for {user_to_toggle.username} to: {perm.can_raise_tickets}")
        return redirect('admin_developer_page')

    layout_blocks = get_or_seed_layout_blocks()
    
    # Get all users to manage permissions
    all_users = User.objects.all().order_by('username')
    teachers_permissions = []
    for user in all_users:
        perm, created = TeacherSupportPermission.objects.get_or_create(user=user)
        display_allowed = True if user.is_superuser else perm.can_raise_tickets
        teachers_permissions.append({
            'user': user,
            'can_raise_tickets': display_allowed,
            'is_superuser': user.is_superuser
        })

    return render(request, 'attendance/developer_page.html', {
        'layout_blocks': layout_blocks,
        'teachers_permissions': teachers_permissions
    })


@login_required(login_url='teacher_login')
@require_POST
def save_layout(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        blocks_data = data.get('blocks', [])
        for block_item in blocks_data:
            bid = block_item.get('id')
            order = block_item.get('order')
            is_visible = block_item.get('is_visible', True)
            AppLayoutBlock.objects.filter(block_id=bid).update(order=order, is_visible=is_visible)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='teacher_login')
@require_POST
def ai_chat_command(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    import re
    import urllib.request
    import urllib.error
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip().lower()
        api_key = data.get('api_key', '').strip()
        
        # Default action structures
        action = None
        target_block = None
        message_response = ""
        
        # 1. Run live Gemini API call if key is provided
        if api_key:
            system_prompt = (
                "You are an AI assistant for a Kindergarten Attendance app layout customizer. "
                "Available blocks are: 'header', 'classroom_tabs', 'stats_banner', 'student_grid'.\n"
                "Understand the user request and map it to a JSON response of this exact schema:\n"
                "{\n"
                "  \"action\": \"hide\" | \"show\" | \"move_top\" | \"move_bottom\" | \"reset\",\n"
                "  \"block\": \"header\" | \"classroom_tabs\" | \"stats_banner\" | \"student_grid\" | null,\n"
                "  \"reply\": \"A friendly short response to the user explaining what you did in child-like tone ✨\"\n"
                "}\n"
                "Only reply with the JSON block. Do not write explanation outside the JSON."
            )
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                req_headers = {'Content-Type': 'application/json'}
                req_payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\nUser request: {user_message}"}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                    }
                }
                
                req = urllib.request.Request(
                    url, 
                    data=json.dumps(req_payload).encode('utf-8'), 
                    headers=req_headers, 
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    text_out = res_data['candidates'][0]['content']['parts'][0]['text']
                    json_res = json.loads(text_out.strip())
                    
                    action = json_res.get('action')
                    target_block = json_res.get('block')
                    message_response = json_res.get('reply', '')
            except Exception as api_err:
                # Fall back to offline parser on API failures
                message_response = f"(Gemini API error, using offline backup) "
        
        # 2. Local Command Parser (Offline Fallback or Direct Matching)
        if not action:
            # Fuzzy match keywords
            if any(k in user_message for k in ['reset', 'default', 'restore']):
                action = 'reset'
                message_response += "Resetting everything back to the default order! 🌟"
            elif any(k in user_message for k in ['hide', 'remove', 'disable', 'delete', 'invisible']):
                action = 'hide'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Poof! I hid the Roster Stats Banner for you. ☁️"
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker']):
                    target_block = 'classroom_tabs'
                    message_response += "Okay, I hid the Classroom Selection Tabs! 🐝"
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Done! I hid the branding Header section. 🏫"
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'kid', 'card']):
                    target_block = 'student_grid'
                    message_response += "Hiding the Student Roster Grid! 🐣"
                else:
                    action = None
            elif any(k in user_message for k in ['show', 'display', 'enable', 'visible', 'add', 'reveal']):
                action = 'show'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Yay! The Roster Stats Banner is back on display. ☀️"
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker']):
                    target_block = 'classroom_tabs'
                    message_response += "Tada! Classroom tabs are now visible. 🦋"
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "The header card is back at the top! 🎒"
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'kid', 'card']):
                    target_block = 'student_grid'
                    message_response += "Making the Student Roster Grid visible again! 🎒"
                else:
                    action = None
            elif any(k in user_message for k in ['top', 'above', 'start', 'first', 'up']):
                action = 'move_top'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Metrics banner moved to the top! 📊"
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker']):
                    target_block = 'classroom_tabs'
                    message_response += "Classroom tabs are sorted to the top! 🐝"
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Header is now placed at the very top of the page! 🏫"
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'kid', 'card']):
                    target_block = 'student_grid'
                    message_response += "Zoom! I moved the Student Roster Grid right to the top! 🚀"
                else:
                    action = None
            elif any(k in user_message for k in ['bottom', 'below', 'end', 'last', 'down']):
                action = 'move_bottom'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Metrics stats are now placed at the bottom. 📉"
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker']):
                    target_block = 'classroom_tabs'
                    message_response += "Classroom tabs are sorted to the bottom! 📉"
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Header is now placed at the very bottom of the page. 📉"
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'kid', 'card']):
                    target_block = 'student_grid'
                    message_response += "Sent the Student Grid to the bottom of the page. 📉"
                else:
                    action = None

            # If fuzzy parsing didn't match any block or action
            if not action or (action != 'reset' and not target_block):
                action = None
                message_response = "Hmm, I didn't quite get that command. Try 'hide stats banner', 'move grid to top', or 'reset layout'! 🧸"
        
        # 3. Execute database actions based on parsed command
        if action:
            if action == 'hide' and target_block:
                AppLayoutBlock.objects.filter(block_id=target_block).update(is_visible=False)
            elif action == 'show' and target_block:
                AppLayoutBlock.objects.filter(block_id=target_block).update(is_visible=True)
            elif action == 'move_top' and target_block:
                # Set target order to 0, shift others, then normalize
                AppLayoutBlock.objects.filter(block_id=target_block).update(order=0)
                all_blocks = list(AppLayoutBlock.objects.all().order_by('order'))
                for idx, b in enumerate(all_blocks):
                    b.order = idx + 1
                    b.save()
            elif action == 'move_bottom' and target_block:
                # Set target order to 99, shift others, then normalize
                AppLayoutBlock.objects.filter(block_id=target_block).update(order=99)
                all_blocks = list(AppLayoutBlock.objects.all().order_by('order'))
                for idx, b in enumerate(all_blocks):
                    b.order = idx + 1
                    b.save()
            elif action == 'reset':
                default_blocks = {'header': 1, 'classroom_tabs': 2, 'stats_banner': 3, 'student_grid': 4}
                for bid, o in default_blocks.items():
                    AppLayoutBlock.objects.filter(block_id=bid).update(order=o, is_visible=True)
        
        # Return state response
        updated_blocks = list(AppLayoutBlock.objects.all().order_by('order').values('block_id', 'title', 'order', 'is_visible'))
        return JsonResponse({
            'success': True,
            'message': message_response,
            'action': action,
            'block': target_block,
            'blocks': updated_blocks
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def schedule_context_processor(request):
    engineers_all = []
    active_engineer = None
    can_raise_support = False
    try:
        # Import dynamically to avoid circular references
        from .models import SupportEngineer, TeacherSupportPermission
        engineers_all = list(SupportEngineer.objects.all())
        active_engineer_id = request.session.get('engineer_id', '')
        if active_engineer_id:
            active_engineer = SupportEngineer.objects.filter(pk=active_engineer_id).first()

        if request.user.is_authenticated:
            if request.user.is_superuser:
                can_raise_support = True
            else:
                perm, created = TeacherSupportPermission.objects.get_or_create(user=request.user)
                can_raise_support = perm.can_raise_tickets
    except Exception:
        pass

    return {
        'schedule_status': get_school_schedule_status(),
        'engineers_all': engineers_all,
        'active_engineer': active_engineer,
        'can_raise_support': can_raise_support,
    }


def ensure_support_seeded():
    if not AssignmentGroup.objects.exists():
        l2 = AssignmentGroup.objects.create(name="L2 Support Team", description="Tier 2 technical issues, app configuration, layout adjustments.")
        l3 = AssignmentGroup.objects.create(name="L3 Support Team", description="Tier 3 database fixes, data migrations, developer APIs.")
        l4 = AssignmentGroup.objects.create(name="L4 Support Team", description="Tier 4 system bugs, core server deployment, critical errors.")
        
        # Seed engineers
        spock = SupportEngineer.objects.create(name="Spock L2", email="spock@vulcan.com")
        spock.groups.add(l2)
        
        data_eng = SupportEngineer.objects.create(name="Data L3", email="data@enterprise.com")
        data_eng.groups.add(l3)
        
        worf = SupportEngineer.objects.create(name="Worf L4", email="worf@klingon.com")
        worf.groups.add(l4)
        
        # Create a default ticket
        t = SupportTicket.objects.create(
            caller="Teacher Jenny",
            subject="Classroom emojis not loading correctly",
            description="The Butterflies classroom layout seems to have lost its custom pink avatar coloring in the grid view. Please restore it.",
            priority="moderate",
            state="new",
            assignment_group=l2
        )
        
        # Seed activity log for it
        TicketActivity.objects.create(
            ticket=t,
            activity_type="work_note",
            author="System Seeder",
            content="Ticket automatically routed to L2 Support Team based on category 'layout adjustments'."
        )
        TicketActivity.objects.create(
            ticket=t,
            activity_type="customer_comment",
            author="System Seeder",
            content="Hello Teacher Jenny, we have logged this ticket and assigned it to our L2 support group. An engineer will follow up shortly."
        )


def has_support_permission(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perm, created = TeacherSupportPermission.objects.get_or_create(user=user)
    return perm.can_raise_tickets


def support_home(request):
    if not request.user.is_authenticated:
        return redirect('teacher_login')
    if not has_support_permission(request.user):
        messages.error(request, "Access denied. You do not have permission to raise support tickets. 🔐")
        return redirect('home')

    ensure_support_seeded()
    
    # Simple search
    search_query = request.GET.get('ticket_number', '').strip()
    if search_query:
        ticket = SupportTicket.objects.filter(number__iexact=search_query).first()
        if ticket:
            return redirect('support_ticket_view', number=ticket.number)
        else:
            messages.error(request, f"No ticket found with number '{search_query}'. Please try again.")
            
    if request.method == 'POST':
        caller = request.POST.get('caller', '').strip()
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'moderate')
        
        if not caller or not subject or not description:
            messages.error(request, "Please fill in all fields.")
        else:
            ticket = SupportTicket.objects.create(
                caller=caller,
                subject=subject,
                description=description,
                priority=priority,
                state='new'
            )
            # Create system comment
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='customer_comment',
                author='System Desk',
                content=f"Ticket '{ticket.number}' has been created successfully. Welcome to our Kindergarten support queue!"
            )
            messages.success(request, f"Ticket {ticket.number} has been created successfully!")
            return redirect('support_ticket_view', number=ticket.number)
            
    # Fetch all created support tickets for list/grid view
    tickets = SupportTicket.objects.all().order_by('-created_at')
    
    return render(request, 'attendance/support_home.html', {
        'tickets': tickets
    })


def support_ticket_view(request, number):
    if not request.user.is_authenticated:
        return redirect('teacher_login')
    if not has_support_permission(request.user):
        messages.error(request, "Access denied. You do not have permission to access support tickets. 🔐")
        return redirect('home')

    ensure_support_seeded()
    ticket = get_object_or_404(SupportTicket, number=number)
    
    if request.method == 'POST':
        author = request.POST.get('author', '').strip()
        comment = request.POST.get('comment', '').strip()
        
        if not author or not comment:
            messages.error(request, "Please fill in your name and message.")
        else:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='customer_comment',
                author=author,
                content=comment
            )
            messages.success(request, "Your comment has been added successfully.")
            return redirect('support_ticket_view', number=ticket.number)
            
    # Fetch public comments only
    activities = ticket.activities.filter(activity_type='customer_comment').order_by('created_at')
    
    return render(request, 'attendance/support_ticket_detail.html', {
        'ticket': ticket,
        'activities': activities
    })


def engineer_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('engineer_id'):
            return redirect('engineer_login')
        from .models import SupportEngineer
        eng = SupportEngineer.objects.filter(pk=request.session['engineer_id'], is_active=True).first()
        if not eng:
            if 'engineer_id' in request.session:
                del request.session['engineer_id']
            messages.error(request, "Your session is invalid or your engineer account has been deactivated.")
            return redirect('engineer_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def engineer_login_view(request):
    if request.session.get('engineer_id'):
        return redirect('engineer_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, "Please enter both email and password.")
        else:
            from .models import SupportEngineer
            eng = SupportEngineer.objects.filter(email__iexact=email).first()
            if eng and eng.password == password:
                if not eng.is_active:
                    messages.error(request, "This account has been deactivated.")
                else:
                    request.session['engineer_id'] = eng.pk
                    messages.success(request, f"Successfully logged in as {eng.name}.")
                    return redirect('engineer_dashboard')
            else:
                messages.error(request, "Invalid email or password.")
                
    return render(request, 'attendance/support/engineer_login.html')


def engineer_logout_view(request):
    if 'engineer_id' in request.session:
        del request.session['engineer_id']
    messages.success(request, "Logged out of IT Tech Services portal.")
    return redirect('engineer_login')


@engineer_login_required
def engineer_dashboard(request):
    ensure_support_seeded()
    
    # Filter by group or state if requested
    group_filter = request.GET.get('group', '')
    state_filter = request.GET.get('state', '')
    priority_filter = request.GET.get('priority', '')
    
    tickets = SupportTicket.objects.all().order_by('-created_at')
    if group_filter:
        tickets = tickets.filter(assignment_group_id=group_filter)
    if state_filter:
        tickets = tickets.filter(state=state_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
        
    groups = AssignmentGroup.objects.all()
    engineers = SupportEngineer.objects.all()
    
    # Active engineer identity for simulation
    active_engineer_id = request.session.get('active_engineer_id', '')
    active_engineer = None
    if active_engineer_id:
        active_engineer = SupportEngineer.objects.filter(pk=active_engineer_id).first()
        
    if request.method == 'POST' and 'set_engineer_id' in request.POST:
        eng_id = request.POST.get('set_engineer_id', '')
        if eng_id:
            request.session['active_engineer_id'] = eng_id
        else:
            if 'active_engineer_id' in request.session:
                del request.session['active_engineer_id']
        return redirect('engineer_dashboard')

    # Compile ticket breakdown per engineer
    engineer_breakdown = []
    for eng in SupportEngineer.objects.filter(is_active=True):
        total_assigned = eng.assigned_tickets.count()
        active_assigned = eng.assigned_tickets.exclude(state__in=['resolved', 'closed']).count()
        grp_names = ", ".join([g.name for g in eng.groups.all()])
        engineer_breakdown.append({
            'name': eng.name,
            'email': eng.email,
            'groups_str': grp_names or "None",
            'total_count': total_assigned,
            'active_count': active_assigned,
        })
    engineer_breakdown.sort(key=lambda x: x['active_count'], reverse=True)

    # Calculate SLA status counts
    sla_breached_count = 0
    active_sla_count = 0
    unassigned_count = SupportTicket.objects.filter(assigned_to__isnull=True).exclude(state__in=['resolved', 'closed']).count()
    for t in SupportTicket.objects.exclude(state__in=['resolved', 'closed']):
        status_info = t.get_sla_status()
        if status_info['status'] == 'breached':
            sla_breached_count += 1
        elif status_info['status'] in ['active', 'warning']:
            active_sla_count += 1

    return render(request, 'attendance/support/engineer_dashboard.html', {
        'tickets': tickets,
        'groups': groups,
        'engineers': engineers,
        'active_engineer': active_engineer,
        'selected_group': group_filter,
        'selected_state': state_filter,
        'selected_priority': priority_filter,
        'engineer_breakdown': engineer_breakdown,
        'sla_breached_count': sla_breached_count,
        'active_sla_count': active_sla_count,
        'unassigned_count': unassigned_count,
    })


@engineer_login_required
def engineer_ticket_detail(request, number):
    ensure_support_seeded()
    ticket = get_object_or_404(SupportTicket, number=number)
    
    # Get active simulation engineer
    active_engineer_id = request.session.get('active_engineer_id', '')
    active_engineer = None
    if active_engineer_id:
        active_engineer = SupportEngineer.objects.filter(pk=active_engineer_id).first()
        
    if request.method == 'POST':
        # Update metadata
        state = request.POST.get('state', '')
        priority = request.POST.get('priority', '')
        group_id = request.POST.get('assignment_group', '')
        assigned_id = request.POST.get('assigned_to', '')
        
        # Determine who is posting
        author_name = active_engineer.name if active_engineer else "Support System"
        
        # Handle fields update
        if state:
            ticket.state = state
        if priority:
            ticket.priority = priority
            
        if group_id:
            ticket.assignment_group_id = group_id
        else:
            ticket.assignment_group = None
            
        if assigned_id:
            ticket.assigned_to_id = assigned_id
        else:
            ticket.assigned_to = None
            
        ticket.save()
        
        # Handle Work Note or Customer Comment
        work_note_content = request.POST.get('work_note', '').strip()
        customer_comment_content = request.POST.get('customer_comment', '').strip()
        
        if work_note_content:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='work_note',
                author=author_name,
                content=work_note_content
            )
            messages.success(request, "Internal Work Note added successfully.")
            
        if customer_comment_content:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='customer_comment',
                author=author_name,
                content=customer_comment_content
            )
            messages.success(request, "Customer Comment added successfully.")
            
        messages.success(request, f"Ticket {ticket.number} updated successfully.")
        return redirect('engineer_ticket_detail', number=ticket.number)
        
    groups = AssignmentGroup.objects.all()
    # If the ticket is assigned to a group, filter engineers of that group
    engineers = SupportEngineer.objects.all()
    if ticket.assignment_group:
        engineers = engineers.filter(groups=ticket.assignment_group)
        
    activities = ticket.activities.all().order_by('-created_at')
    
    return render(request, 'attendance/support/engineer_ticket_detail.html', {
        'ticket': ticket,
        'groups': groups,
        'engineers': engineers,
        'activities': activities,
        'active_engineer': active_engineer,
    })


@engineer_login_required
def engineer_list(request):
    ensure_support_seeded()
    engineers = SupportEngineer.objects.all()
    return render(request, 'attendance/support/engineer_list.html', {
        'engineers': engineers
    })


@engineer_login_required
def engineer_create(request):
    ensure_support_seeded()
    groups = AssignmentGroup.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        group_ids = request.POST.getlist('groups')
        is_active = request.POST.get('is_active', '') == 'true'
        
        if not name or not email:
            messages.error(request, "Please enter name and email.")
        else:
            eng = SupportEngineer.objects.create(
                name=name,
                email=email,
                is_active=is_active
            )
            if group_ids:
                eng.groups.set(group_ids)
            messages.success(request, f"Engineer {name} created successfully.")
            return redirect('engineer_list')
            
    return render(request, 'attendance/support/engineer_form.html', {
        'groups': groups,
        'action': 'Create'
    })


@engineer_login_required
def engineer_edit(request, pk):
    ensure_support_seeded()
    engineer = get_object_or_404(SupportEngineer, pk=pk)
    groups = AssignmentGroup.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        group_ids = request.POST.getlist('groups')
        is_active = request.POST.get('is_active', '') == 'true'
        
        if not name or not email:
            messages.error(request, "Please enter name and email.")
        else:
            engineer.name = name
            engineer.email = email
            engineer.is_active = is_active
            engineer.save()
            engineer.groups.set(group_ids)
            messages.success(request, f"Engineer {name} updated successfully.")
            return redirect('engineer_list')
            
    return render(request, 'attendance/support/engineer_form.html', {
        'engineer': engineer,
        'groups': groups,
        'action': 'Edit'
    })


@engineer_login_required
def engineer_delete(request, pk):
    ensure_support_seeded()
    engineer = get_object_or_404(SupportEngineer, pk=pk)
    name = engineer.name
    if request.method == 'POST':
        engineer.delete()
        messages.success(request, f"Engineer {name} deleted successfully.")
        return redirect('engineer_list')
    return render(request, 'attendance/support/engineer_confirm_delete.html', {
        'engineer': engineer
    })


@engineer_login_required
def group_list(request):
    ensure_support_seeded()
    groups = AssignmentGroup.objects.all()
    return render(request, 'attendance/support/group_list.html', {
        'groups': groups
    })


@engineer_login_required
def group_create(request):
    ensure_support_seeded()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Please enter a group name.")
        else:
            try:
                AssignmentGroup.objects.create(name=name, description=description)
                messages.success(request, f"Group {name} created successfully.")
                return redirect('group_list')
            except Exception as e:
                messages.error(request, f"Error creating group: {e}")
                
    return render(request, 'attendance/support/group_form.html', {
        'action': 'Create'
    })


@engineer_login_required
def group_edit(request, pk):
    ensure_support_seeded()
    group = get_object_or_404(AssignmentGroup, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Please enter a group name.")
        else:
            try:
                group.name = name
                group.description = description
                group.save()
                messages.success(request, f"Group {name} updated successfully.")
                return redirect('group_list')
            except Exception as e:
                messages.error(request, f"Error updating group: {e}")
                
    return render(request, 'attendance/support/group_form.html', {
        'group': group,
        'action': 'Edit'
    })


@engineer_login_required
def group_delete(request, pk):
    ensure_support_seeded()
    group = get_object_or_404(AssignmentGroup, pk=pk)
    name = group.name
    if request.method == 'POST':
        group.delete()
        messages.success(request, f"Group {name} deleted successfully.")
        return redirect('group_list')
    return render(request, 'attendance/support/group_confirm_delete.html', {
        'group': group
    })


@engineer_login_required
def identity_manager(request):
    ensure_support_seeded()
    from .models import SupportEngineer, AssignmentGroup, TeacherSupportPermission
    from django.contrib.auth.models import User

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_teacher_permission':
            user_id = request.POST.get('user_id')
            user_to_toggle = get_object_or_404(User, pk=user_id)
            perm, created = TeacherSupportPermission.objects.get_or_create(user=user_to_toggle)
            perm.can_raise_tickets = not perm.can_raise_tickets
            perm.save()
            messages.success(request, f"Updated support ticket permissions for {user_to_toggle.username} to: {perm.can_raise_tickets}")
            return redirect('identity_manager')
            
        elif action == 'update_engineer_groups':
            engineer_id = request.POST.get('engineer_id')
            engineer = get_object_or_404(SupportEngineer, pk=engineer_id)
            group_ids = request.POST.getlist('groups')
            # Convert string IDs to integers
            group_pks = [int(gid) for gid in group_ids if gid.isdigit()]
            # Set the engineer's groups
            engineer.groups.set(AssignmentGroup.objects.filter(pk__in=group_pks))
            engineer.save()
            messages.success(request, f"Updated assignment groups for engineer {engineer.name}.")
            return redirect('identity_manager')

        elif action == 'toggle_staff_status':
            user_id = request.POST.get('user_id')
            user_to_toggle = get_object_or_404(User, pk=user_id)
            user_to_toggle.is_staff = not user_to_toggle.is_staff
            user_to_toggle.save()
            messages.success(request, f"Updated admin (is_staff) status for {user_to_toggle.username} to: {user_to_toggle.is_staff}")
            return redirect('identity_manager')

    # Fetch users, engineers, groups
    users = User.objects.all().order_by('username')
    engineers = SupportEngineer.objects.all().order_by('name')
    groups = AssignmentGroup.objects.all().order_by('name')

    # Build template context helper mapping permissions
    user_perms = []
    for u in users:
        perm, created = TeacherSupportPermission.objects.get_or_create(user=u)
        user_perms.append({
            'user': u,
            'can_raise': perm.can_raise_tickets or u.is_superuser
        })

    return render(request, 'attendance/support/identity_manager.html', {
        'user_perms': user_perms,
        'engineers': engineers,
        'groups': groups,
    })



