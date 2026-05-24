import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kindergarten_attendance.settings')
django.setup()

from attendance.models import Student, Attendance

def seed_database():
    print("🌱 Starting database seeding...")
    
    # Seed teacher user
    from django.contrib.auth.models import User
    User.objects.filter(username='teacher').delete()
    teacher = User.objects.create_user(username='teacher', email='teacher@school.com', password='teacher123')
    teacher.is_staff = True
    teacher.is_superuser = True
    teacher.save()
    print("👤 Created default teacher account: teacher / teacher123")
    
    # Clean existing data
    print("🧹 Cleaning out existing student roster and attendance lists...")
    Attendance.objects.all().delete()
    Student.objects.all().delete()
    
    # Define adorable kids records
    mock_students = [
        # Bumblebees Classroom 🐝
        {
            "first_name": "Leo",
            "last_name": "Lion",
            "classroom": "Bumblebees",
            "avatar_emoji": "🦁",
            "avatar_color": "#FDFFB6" # Pastel Yellow
        },
        {
            "first_name": "Toby",
            "last_name": "Tiger",
            "classroom": "Bumblebees",
            "avatar_emoji": "🐯",
            "avatar_color": "#FFD6A5" # Pastel Orange
        },
        {
            "first_name": "Ella",
            "last_name": "Elephant",
            "classroom": "Bumblebees",
            "avatar_emoji": "🐘",
            "avatar_color": "#A0C4FF" # Pastel Blue
        },
        {
            "first_name": "Polly",
            "last_name": "Panda",
            "classroom": "Bumblebees",
            "avatar_emoji": "🐼",
            "avatar_color": "#FFC6FF" # Pastel Pink
        },
        
        # Butterflies Classroom 🦋
        {
            "first_name": "Felix",
            "last_name": "Fox",
            "classroom": "Butterflies",
            "avatar_emoji": "🦊",
            "avatar_color": "#FFADAD" # Pastel Red
        },
        {
            "first_name": "Katy",
            "last_name": "Koala",
            "classroom": "Butterflies",
            "avatar_emoji": "🐨",
            "avatar_color": "#BDB2FF" # Pastel Purple
        },
        {
            "first_name": "Danny",
            "last_name": "Dino",
            "classroom": "Butterflies",
            "avatar_emoji": "🦖",
            "avatar_color": "#CAFFBF" # Pastel Green
        },
        {
            "first_name": "Una",
            "last_name": "Unicorn",
            "classroom": "Butterflies",
            "avatar_emoji": "🦄",
            "avatar_color": "#FFC6FF" # Pastel Pink
        },
        
        # Ladybugs Classroom 🐞
        {
            "first_name": "Bella",
            "last_name": "Bunny",
            "classroom": "Ladybugs",
            "avatar_emoji": "🐰",
            "avatar_color": "#FDFFB6" # Pastel Yellow
        },
        {
            "first_name": "Freddy",
            "last_name": "Frog",
            "classroom": "Ladybugs",
            "avatar_emoji": "🐸",
            "avatar_color": "#CAFFBF" # Pastel Green
        },
        {
            "first_name": "Ollie",
            "last_name": "Owl",
            "classroom": "Ladybugs",
            "avatar_emoji": "🦉",
            "avatar_color": "#BDB2FF" # Pastel Purple
        },
        {
            "first_name": "Chloe",
            "last_name": "Crab",
            "classroom": "Ladybugs",
            "avatar_emoji": "🦀",
            "avatar_color": "#FFADAD" # Pastel Red
        }
    ]
    
    # Save to Database
    count = 0
    for child in mock_students:
        pin = f"{1000 + count + 1}"
        student = Student.objects.create(
            first_name=child["first_name"],
            last_name=child["last_name"],
            classroom=child["classroom"],
            avatar_emoji=child["avatar_emoji"],
            avatar_color=child["avatar_color"],
            pin_code=pin
        )
        print(f"🎒 Created student: {student.full_name} in {student.classroom} ({student.avatar_emoji}) - PIN: {student.pin_code}")
        count += 1
        
    print(f"✨ Seeding complete! Added {count} kids into the database successfully.")

if __name__ == "__main__":
    seed_database()
