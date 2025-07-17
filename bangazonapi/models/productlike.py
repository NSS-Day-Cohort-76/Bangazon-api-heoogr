from django.db import models
from django.contrib.auth.models import User
from .product import Product
from .customer import Customer


class ProductLike(models.Model):
    """Model for tracking likes on products"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("product", "customer"),)
