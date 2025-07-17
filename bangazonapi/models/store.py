from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Store(models.Model):
    seller = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store') # this makes sure there is one store per user 
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name
