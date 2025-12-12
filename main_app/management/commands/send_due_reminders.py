from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from main_app.models import Reservation

class Command(BaseCommand):
    help = 'Send email reminders for games due in 2 days'

    def handle(self, *args, **options):
        two_days_from_now = timezone.now().date() + timedelta(days=2)
        
        reservations = Reservation.objects.filter(
            due_date=two_days_from_now,
            status='accepted',
            picked_up_date__isnull=False,
            returned_date__isnull=True
        )
        
        for reservation in reservations:
            subject = f'Reminder: {reservation.game_copy.game.name} is due in 2 days'
            message = f'''
            Hi {reservation.borrower.display_name},
            
            This is a reminder that the game "{reservation.game_copy.game.name}" 
            borrowed from {reservation.owner.display_name} is due on {reservation.due_date}.
            
            Please make arrangements to return the game on time.
            
            Thank you for using GeekLoop!
            '''
            
            send_mail(
                subject,
                message,
                'noreply@geekloop.com',
                [reservation.borrower.user.email],
                fail_silently=False,
            )