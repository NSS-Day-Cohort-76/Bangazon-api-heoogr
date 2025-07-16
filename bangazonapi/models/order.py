"""Customer order model"""

from django.db import models
from .customer import Customer
from .payment import Payment
from django.utils import timezone


class Order(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True
    )
    payment_type = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True)
    created_date = models.DateField(
        default=timezone.now,
    )
