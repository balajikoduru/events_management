from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Event, Invitation

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 'capacity', 'is_public', 'image']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['name', 'email']

class BulkInvitationForm(forms.Form):
    emails = forms.CharField(widget=forms.Textarea, help_text="Enter one email per line")
    
    def clean_emails(self):
        data = self.cleaned_data['emails']
        emails = [email.strip() for email in data.split('\n') if email.strip()]
        
        # Validate each email
        for email in emails:
            if not forms.EmailField().clean(email):
                raise forms.ValidationError(f"Invalid email: {email}")
        
        return emails

class RSVPForm(forms.Form):
    CHOICES = [
        ('accepted', 'Yes, I will attend'),
        ('declined', 'No, I cannot attend')
    ]
    response = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
