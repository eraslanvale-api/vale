from django.db import models
import uuid
from django.conf import settings

# Create your models here.
class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
    related_name="notifications")
    title = models.CharField(max_length=255, blank=True,null=True)
    message = models.CharField(max_length=255, blank=True,null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.title} - {self.message} - {self.is_read} - {self.created_at}"
    