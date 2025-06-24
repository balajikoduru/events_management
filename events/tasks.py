from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import datetime

@shared_task
def send_invitation_email(invitation_id, invitation_url):
    from .models import Invitation
    
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        event = invitation.event
        
        subject = f"You're invited to {event.title}"
        message = f"""
        Hello {invitation.name},
        
        You have been invited to {event.title} by {event.created_by.username}.
        
        Event Details:
        - Date: {event.start_date.strftime('%A, %B %d, %Y')}
        - Time: {event.start_date.strftime('%I:%M %p')} - {event.end_date.strftime('%I:%M %p')}
        - Location: {event.location}
        
        Please RSVP by clicking the link below:
        {invitation_url}
        
        We hope to see you there!
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )
        
        return f"Invitation email sent to {invitation.email}"
    
    except Exception as e:
        return f"Error sending invitation email: {str(e)}"

@shared_task
def send_reminder_email(invitation_id):
    from .models import Invitation
    
    try:
        invitation = Invitation.objects.get(id=invitation_id, status='accepted')
        event = invitation.event
        
        subject = f"Reminder: {event.title} is tomorrow"
        message = f"""
        Hello {invitation.name},
        
        This is a friendly reminder that {event.title} is tomorrow!
        
        Event Details:
        - Date: {event.start_date.strftime('%A, %B %d, %Y')}
        - Time: {event.start_date.strftime('%I:%M %p')} - {event.end_date.strftime('%I:%M %p')}
        - Location: {event.location}
        
        Your QR code for check-in is attached to this email.
        
        We look forward to seeing you!
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )
        
        return f"Reminder email sent to {invitation.email}"
    
    except Exception as e:
        return f"Error sending reminder email: {str(e)}"

@shared_task
def schedule_reminders():
    from .models import Event, Invitation
    
    # Get events happening tomorrow
    tomorrow = timezone.now().date() + datetime.timedelta(days=1)
    events = Event.objects.filter(
        start_date__date=tomorrow,
        end_date__gte=timezone.now()
    )
    
    for event in events:
        # Get accepted invitations
        invitations = Invitation.objects.filter(event=event, status='accepted')
        
        for invitation in invitations:
            send_reminder_email.delay(invitation.id)
    
    return f"Scheduled reminders for {len(events)} events"
