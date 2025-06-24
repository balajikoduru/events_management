from django.contrib import admin
from .models import Event, Invitation

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'created_by', 'is_public')
    list_filter = ('is_public', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'event', 'status', 'checked_in')
    list_filter = ('status', 'checked_in')
    search_fields = ('name', 'email')
    date_hierarchy = 'created_at'
