from django.db import models


class OrderProduct(models.Model):

    order = models.ForeignKey("Order",
                              on_delete=models.SET_NULL,
                              related_name="lineitems", null=True)

    product = models.ForeignKey("Product",
                                on_delete=models.DO_NOTHING,
                                related_name="lineitems")
    
    quantity = models.PositiveIntegerField(default=1)
