from django.db import models
from django.contrib.auth.models import User

class Agent(models.Model):
    uuid = models.CharField(max_length=255, unique=True)
    ip = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Agent {self.uuid}"
