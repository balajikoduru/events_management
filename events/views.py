from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from .models import Event, Invitation
from .forms import EventForm, InvitationForm, BulkInvitationForm, RSVPForm, CustomUserCreationForm
from .tasks import send_invitation_email, send_reminder_email

def home(request):
    upcoming_events = Event.objects.filter(
        Q(is_public=True) | Q(invitations__user=request.user.id if request.user.is_authenticated else None),
        end_date__gte=timezone.now()
    ).distinct().order_by('start_date')[:5]
    
    return render(request, 'events/home.html', {
        'upcoming_events': upcoming_events
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # Events created by the user
    created_events = Event.objects.filter(created_by=request.user).order_by('-start_date')
    
    # Events the user is invited to
    invited_events = Event.objects.filter(
        invitations__user=request.user
    ).exclude(created_by=request.user).order_by('-start_date')
    
    # Filter parameters
    event_filter = request.GET.get('filter', 'upcoming')
    
    if event_filter == 'past':
        created_events = created_events.filter(end_date__lt=timezone.now())
        invited_events = invited_events.filter(end_date__lt=timezone.now())
    elif event_filter == 'upcoming':
        created_events = created_events.filter(end_date__gte=timezone.now())
        invited_events = invited_events.filter(end_date__gte=timezone.now())
    
    return render(request, 'events/dashboard.html', {
        'created_events': created_events,
        'invited_events': invited_events,
        'event_filter': event_filter
    })

@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, f"Event '{event.title}' created successfully!")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    
    return render(request, 'events/event_form.html', {'form': form})

@login_required
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Event '{event.title}' updated successfully!")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/event_form.html', {'form': form, 'event': event})

@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f"Event '{event_title}' deleted successfully!")
        return redirect('dashboard')
    
    return render(request, 'events/event_confirm_delete.html', {'event': event})

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    # Check if the event is public or the user is invited or is the creator
    is_invited = False
    invitation = None
    
    if request.user.is_authenticated:
        is_creator = event.created_by == request.user
        try:
            invitation = Invitation.objects.get(event=event, user=request.user)
            is_invited = True
        except Invitation.DoesNotExist:
            pass
    else:
        is_creator = False
    
    if not event.is_public and not is_invited and not is_creator:
        messages.error(request, "You don't have permission to view this event.")
        return redirect('home')
    
    # Get attendees
    attendees = Invitation.objects.filter(event=event, status='accepted')
    
    return render(request, 'events/event_detail.html', {
        'event': event,
        'is_creator': is_creator,
        'is_invited': is_invited,
        'invitation': invitation,
        'attendees': attendees
    })

@login_required
def invite_to_event(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            
            # Check if user with this email exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = request.user  # Fallback to event creator
            
            # Check if invitation already exists
            if Invitation.objects.filter(event=event, email=email).exists():
                messages.error(request, f"An invitation for {email} already exists.")
            else:
                invitation = Invitation.objects.create(
                    event=event,
                    user=user,
                    email=email,
                    name=name
                )
                
                # Send invitation email asynchronously
                invitation_url = request.build_absolute_uri(
                    reverse('rsvp', kwargs={'uuid': invitation.uuid})
                )
                send_invitation_email.delay(invitation.id, invitation_url)
                
                messages.success(request, f"Invitation sent to {email}!")
            
            return redirect('event_invitations', pk=event.pk)
    else:
        form = InvitationForm()
    
    return render(request, 'events/invite_form.html', {
        'form': form,
        'event': event
    })

@login_required
def bulk_invite(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = BulkInvitationForm(request.POST)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            success_count = 0
            
            for email in emails:
                # Check if invitation already exists
                if Invitation.objects.filter(event=event, email=email).exists():
                    continue
                
                # Check if user with this email exists
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = request.user  # Fallback to event creator
                
                invitation = Invitation.objects.create(
                    event=event,
                    user=user,
                    email=email,
                    name=email.split('@')[0]  # Use part of email as name
                )
                
                # Send invitation email asynchronously
                invitation_url = request.build_absolute_uri(
                    reverse('rsvp', kwargs={'uuid': invitation.uuid})
                )
                send_invitation_email.delay(invitation.id, invitation_url)
                
                success_count += 1
            
            messages.success(request, f"{success_count} invitations sent successfully!")
            return redirect('event_invitations', pk=event.pk)
    else:
        form = BulkInvitationForm()
    
    return render(request, 'events/bulk_invite_form.html', {
        'form': form,
        'event': event
    })

@login_required
def event_invitations(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    invitations = Invitation.objects.filter(event=event).order_by('-created_at')
    
    return render(request, 'events/event_invitations.html', {
        'event': event,
        'invitations': invitations
    })

def rsvp(request, uuid):
    invitation = get_object_or_404(Invitation, uuid=uuid)
    event = invitation.event
    
    if event.is_past:
        messages.error(request, "This event has already ended.")
        return redirect('home')
    
    if request.method == 'POST':
        form = RSVPForm(request.POST)
        if form.is_valid():
            response = form.cleaned_data['response']
            invitation.status = response
            invitation.save()
            
            if response == 'accepted':
                messages.success(request, f"You have successfully RSVP'd to {event.title}!")
            else:
                messages.info(request, f"You have declined the invitation to {event.title}.")
            
            if request.user.is_authenticated:
                return redirect('dashboard')
            else:
                return redirect('home')
    else:
        form = RSVPForm()
    
    return render(request, 'events/rsvp_form.html', {
        'form': form,
        'invitation': invitation,
        'event': event
    })

@login_required
def check_in(request, pk, invitation_id):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    invitation = get_object_or_404(Invitation, id=invitation_id, event=event)
    
    if invitation.status != 'accepted':
        messages.error(request, f"{invitation.name} has not accepted the invitation.")
    elif invitation.checked_in:
        messages.info(request, f"{invitation.name} has already checked in at {invitation.checked_in_at}.")
    else:
        invitation.checked_in = True
        invitation.checked_in_at = timezone.now()
        invitation.save()
        messages.success(request, f"{invitation.name} has been checked in successfully!")
    
    return redirect('event_invitations', pk=event.pk)

@login_required
def scan_qr(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    return render(request, 'events/scan_qr.html', {'event': event})

@login_required
def verify_qr(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk, created_by=request.user)
        uuid = request.POST.get('uuid')
        
        try:
            invitation = Invitation.objects.get(uuid=uuid, event=event)
            
            if invitation.status != 'accepted':
                return HttpResponse(f"Error: {invitation.name} has not accepted the invitation.", status=400)
            
            if invitation.checked_in:
                return HttpResponse(f"{invitation.name} already checked in at {invitation.checked_in_at}.", status=200)
            
            invitation.checked_in = True
            invitation.checked_in_at = timezone.now()
            invitation.save()
            
            return HttpResponse(f"{invitation.name} checked in successfully!", status=200)
        
        except Invitation.DoesNotExist:
            return HttpResponse("Invalid QR code or invitation not found.", status=404)
    
    return HttpResponse("Method not allowed", status=405)
