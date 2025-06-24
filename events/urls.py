from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Event CRUD
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/update/', views.event_update, name='event_update'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    
    # Invitations
    path('events/<int:pk>/invite/', views.invite_to_event, name='invite_to_event'),
    path('events/<int:pk>/bulk-invite/', views.bulk_invite, name='bulk_invite'),
    path('events/<int:pk>/invitations/', views.event_invitations, name='event_invitations'),
    path('rsvp/<uuid:uuid>/', views.rsvp, name='rsvp'),
    
    # Check-in
    path('events/<int:pk>/check-in/<int:invitation_id>/', views.check_in, name='check_in'),
    path('events/<int:pk>/scan-qr/', views.scan_qr, name='scan_qr'),
    path('events/<int:pk>/verify-qr/', views.verify_qr, name='verify_qr'),
]
