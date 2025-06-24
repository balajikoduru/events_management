import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.contrib.auth.models import User
from django.core.files import File
from django.utils import timezone
from PIL import Image

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    capacity = models.PositiveIntegerField(default=0)  # 0 means unlimited
    is_public = models.BooleanField(default=False)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_past(self):
        return self.end_date < timezone.now()
    
    @property
    def attendee_count(self):
        return self.invitations.filter(status='accepted').count()
    
    @property
    def spots_left(self):
        if self.capacity == 0:  # Unlimited capacity
            return float('inf')
        return max(0, self.capacity - self.attendee_count)

class Invitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['event', 'email']
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.uuid))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"qr_{self.uuid}.png", File(buffer), save=False)
