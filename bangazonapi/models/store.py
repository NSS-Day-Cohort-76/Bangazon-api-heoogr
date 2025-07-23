from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Store(models.Model):
    seller = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="store"
    )  # this makes sure there is one store per user
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return str(self.name) if self.name else "Unnamed Store"

    @property
    def can_be_favorited(self):
        try:
            return self._can_be_favorited
        except AttributeError:
            return False

    @can_be_favorited.setter
    def can_be_favorited(self, value):
        """Set whether this store can be favorited by the current user."""
        self._can_be_favorited = value
