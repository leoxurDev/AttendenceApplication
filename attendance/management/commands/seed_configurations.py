from django.core.management.base import BaseCommand
from attendance.models import ClassroomOption, AvatarEmoji, AvatarColor


class Command(BaseCommand):
    help = 'Seed initial configuration options (classrooms, avatar emojis, colors)'

    def handle(self, *args, **options):
        # Classroom options
        classrooms = [
            {'emoji': '🐝', 'name': 'Bumblebees', 'description': 'Pre-KG', 'order': 0},
            {'emoji': '🦋', 'name': 'Butterflies', 'description': 'LKG', 'order': 1},
            {'emoji': '🐞', 'name': 'Ladybugs', 'description': 'UKG', 'order': 2},
            {'emoji': '🪰', 'name': 'Dragonflies', 'description': '1st Grade', 'order': 3},
            {'emoji': '🍯', 'name': 'Honeybees', 'description': '2nd Grade', 'order': 4},
            {'emoji': '✨', 'name': 'Fireflies', 'description': '3rd Grade', 'order': 5},
            {'emoji': '🦗', 'name': 'Grasshoppers', 'description': '4th Grade', 'order': 6},
            {'emoji': '🐛', 'name': 'Caterpillars', 'description': '5th Grade', 'order': 7},
        ]
        
        for classroom in classrooms:
            obj, created = ClassroomOption.objects.get_or_create(
                name=classroom['name'],
                defaults={
                    'emoji': classroom['emoji'],
                    'description': classroom['description'],
                    'order': classroom['order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created classroom: {obj}"))
            else:
                self.stdout.write(f"Classroom already exists: {obj}")
        
        # Avatar emojis
        emojis = [
            {'emoji': '🦁', 'name': 'Lion', 'order': 0},
            {'emoji': '🐯', 'name': 'Tiger', 'order': 1},
            {'emoji': '🐘', 'name': 'Elephant', 'order': 2},
            {'emoji': '🐼', 'name': 'Panda', 'order': 3},
            {'emoji': '🦊', 'name': 'Fox', 'order': 4},
            {'emoji': '🐨', 'name': 'Koala', 'order': 5},
            {'emoji': '🦖', 'name': 'Dino', 'order': 6},
            {'emoji': '🦄', 'name': 'Unicorn', 'order': 7},
            {'emoji': '🐰', 'name': 'Bunny', 'order': 8},
            {'emoji': '🐸', 'name': 'Frog', 'order': 9},
            {'emoji': '🦉', 'name': 'Owl', 'order': 10},
            {'emoji': '🐝', 'name': 'Bee', 'order': 11},
            {'emoji': '🦋', 'name': 'Butterfly', 'order': 12},
            {'emoji': '🐳', 'name': 'Whale', 'order': 13},
            {'emoji': '🦀', 'name': 'Crab', 'order': 14},
            {'emoji': '🐬', 'name': 'Dolphin', 'order': 15},
        ]
        
        for emoji in emojis:
            obj, created = AvatarEmoji.objects.get_or_create(
                emoji=emoji['emoji'],
                defaults={'name': emoji['name'], 'order': emoji['order']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created emoji: {obj}"))
            else:
                self.stdout.write(f"Emoji already exists: {obj}")
        
        # Avatar colors
        colors = [
            {'hex_code': '#FFADAD', 'name': 'Pastel Red', 'order': 0},
            {'hex_code': '#FFD6A5', 'name': 'Pastel Orange', 'order': 1},
            {'hex_code': '#2F2F2F', 'name': 'Pastel Black', 'order': 2},
            {'hex_code': '#FDFFB6', 'name': 'Pastel Yellow', 'order': 3},
            {'hex_code': '#CAFFBF', 'name': 'Pastel Green', 'order': 4},
            {'hex_code': '#9BF6FF', 'name': 'Pastel Cyan', 'order': 5},
            {'hex_code': '#A0C4FF', 'name': 'Pastel Blue', 'order': 6},
            {'hex_code': '#BDB2FF', 'name': 'Pastel Purple', 'order': 7},
            {'hex_code': '#FFC6FF', 'name': 'Pastel Pink', 'order': 8},
        ]
        
        for color in colors:
            obj, created = AvatarColor.objects.get_or_create(
                hex_code=color['hex_code'],
                defaults={'name': color['name'], 'order': color['order']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created color: {obj}"))
            else:
                self.stdout.write(f"Color already exists: {obj}")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded all configurations!'))
