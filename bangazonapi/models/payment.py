from django.db import models
from .customer import Customer
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE

class Payment(SafeDeleteModel):

    _safedelete_policy = SOFT_DELETE
    merchant_name = models.CharField(max_length=25,)
    account_number = models.CharField(max_length=25)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, related_name="payment_types")
    expiration_date = models.DateField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)


    @property
    def obscured_num(self):
        """Return obscured account number for security"""
        if self.account_number and len(self.account_number) > 4:
            return "*" * (len(self.account_number) - 4) + self.account_number[-4:]
        return self.account_number or ""