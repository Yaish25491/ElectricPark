from django.core.management.base import BaseCommand
from myapp.models import Profile, User  # Import your Profile and User models

class Command(BaseCommand):
    help = 'Create Profile instances for existing users'

    def handle(self, *args, **options):
        # Get all existing users
        users = User.objects.all()

        # Create a Profile for each user
        for user in users:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Profile for user: {user.username}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Profile already exists for user: {user.username}'))
